"""
Adaptive Video Memory Compression and Streaming Pipeline

This module provides classes and functions to:
- Compress and decompress data (e.g., model weights, textures) using FFT, DCT, and DCT-TopK transforms.
- Dynamically select compression factors based on GPU VRAM capacity.
- Stream compressed model parameters from CPU to one or multiple GPUs, expanding effective VRAM for ML and rendering workloads.
"""

# curve_memory_encoder.py
import numpy as np
from scipy.fftpack import dct, idct

class CurveMemoryEncoder:
    """
    Implements transform-based compression and decompression:
      - FFT (complex64 based)
      - DCT (real-valued)
      - DCT-TopK (magnitude-based pruning)
    """

    @staticmethod
    def gpu_mem(byte_count: int) -> float:
        """Convert a byte count to MiB."""
        return byte_count / (1024 ** 2)

    @staticmethod
    def encode_fft(data: np.ndarray, factor: int = 4):
        """Compress using real FFT and cast to complex64."""
        orig = data.size
        k = orig // factor
        fft_coeffs = np.fft.rfft(data).astype(np.complex64)
        return fft_coeffs[:k], {'method':'fft','original_size':orig,'compressed_size':k}

    @staticmethod
    def decode_fft(coeffs: np.ndarray, meta: dict) -> np.ndarray:
        """Reconstruct data from truncated FFT."""
        orig = meta['original_size']
        full = np.zeros(orig//2+1, dtype=np.complex64)
        full[:coeffs.shape[0]] = coeffs
        return np.fft.irfft(full, n=orig).astype(np.float32)

    @staticmethod
    def encode_dct(data: np.ndarray, factor: int = 4):
        """Compress using 1D DCT-II (ortho norm)."""
        orig = data.size
        k = orig // factor
        coeffs = dct(data, norm='ortho')[:k].astype(np.float32)
        return coeffs, {'method':'dct','original_size':orig,'k':k}

    @staticmethod
    def decode_dct(coeffs: np.ndarray, meta: dict) -> np.ndarray:
        """Reconstruct data from truncated DCT."""
        orig, k = meta['original_size'], meta['k']
        full = np.zeros(orig, dtype=np.float32)
        full[:k] = coeffs
        return idct(full, norm='ortho').astype(np.float32)

    @staticmethod
    def encode_dct_topk(data: np.ndarray, factor: int = 4):
        """Compress by keeping top-k DCT coefficients by magnitude."""
        orig = data.size
        k = orig // factor
        coeffs = dct(data, norm='ortho').ravel()
        idx = np.argpartition(np.abs(coeffs), -k)[-k:]
        vals = coeffs[idx].astype(np.float32)
        return vals, {'method':'dct_topk','original_size':orig,'idx':idx,'shape':data.shape}

    @staticmethod
    def decode_dct_topk(vals: np.ndarray, meta: dict) -> np.ndarray:
        """Reconstruct data from top-k DCT representation."""
        orig = meta['original_size']
        full = np.zeros(orig, dtype=np.float32)
        full[meta['idx']] = vals
        return idct(full.reshape(meta['shape']), norm='ortho').astype(np.float32)

# cpu_to_gpu_stream.py
import torch
import numpy as np
import os
from torchvision import models, transforms
from PIL import Image
from curve_memory_encoder import CurveMemoryEncoder as Cme

class ModelStreamer:
    """
    Handles streaming of model weights from CPU to GPU with adaptive compression.

    Attributes:
      factor: base compression factor (overridden per GPU by free VRAM)
    """

    def __init__(self, base_factor: int = 4):
        assert torch.cuda.is_available(), "CUDA required"
        self.base_factor = base_factor
        self.encoder = Cme()

    def gpu_free_mem(self, idx: int) -> float:
        prop = torch.cuda.get_device_properties(idx)
        used = torch.cuda.memory_allocated(idx)
        return (prop.total_memory - used) / (1024 ** 2)

    def choose_factor(self, byte_count: int, free_mib: float) -> int:
        free_bytes = free_mib * 1024**2
        return max(1, int(np.ceil(byte_count / free_bytes)))

    def stream_conv1(self, device_idx: int):
        dev = f'cuda:{device_idx}'
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT).to(dev).eval()
        w = model.conv1.weight.data.cpu().numpy().astype(np.float32).ravel()
        factor = self.choose_factor(w.nbytes, self.gpu_free_mem(device_idx))
        print(f"GPU {device_idx}: free VRAM={self.gpu_free_mem(device_idx):.1f} MiB, factor={factor}")
        comp, meta = self.encoder.encode_dct_topk(w, factor)
        rec = self.encoder.decode_dct_topk(comp, meta).reshape(model.conv1.weight.shape)
        model.conv1.weight.data.copy_(torch.from_numpy(rec).to(dev))
        return model, factor

    def run(self):
        # Reset and clear cache
        for i in range(torch.cuda.device_count()):
            torch.cuda.reset_peak_memory_stats(i)
        torch.cuda.empty_cache()

        # Baseline mem
        base = sum(torch.cuda.memory_allocated(i) for i in range(torch.cuda.device_count()))

        # Stream to all GPUs
        models_list, factors = [], []
        for i in range(torch.cuda.device_count()):
            m, f = self.stream_conv1(i)
            models_list.append(m); factors.append(f)
        post = sum(torch.cuda.memory_allocated(i) for i in range(torch.cuda.device_count()))

        print(f"Baseline total GPU memory: {Cme.gpu_mem(base):.2f} MiB")
        print(f"After streaming:            {Cme.gpu_mem(post):.2f} MiB")
        print(f"Used factors: {factors}")

        # Inference test
        pre = transforms.Compose([transforms.Resize(224),transforms.CenterCrop(224),transforms.ToTensor()])
        img = Image.open(os.path.join(os.getcwd(),'sample.jpg')).convert('RGB')
        inp = pre(img).unsqueeze(0)
        agree = 0
        for i,m in enumerate(models_list):
            p1 = m(inp.to(f'cuda:{i}')).argmax(1).cpu().item()
            base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT).to(f'cuda:{i}').eval()
            p2 = base_model(inp.to(f'cuda:{i}')).argmax(1).cpu().item()
            agree += (p1==p2)
        print(f"Top-1 agreement: {agree}/{len(models_list)}")

        # Texture test
        gray = np.array(img.convert('L').resize((256,256)),np.float32)/255.0
        comp, meta = self.encoder.encode_dct_topk(gray.ravel(), factors[0])
        rec = self.encoder.decode_dct_topk(comp, meta).reshape(gray.shape)
        from skimage.metrics import peak_signal_noise_ratio as psnr, structural_similarity as ssim
        print(f"Texture PSNR: {psnr(gray, rec, data_range=1.0):.2f} dB, SSIM: {ssim(gray, rec, data_range=1.0):.4f}")

if __name__=='__main__':
    streamer = ModelStreamer(base_factor=4)
    streamer.run()

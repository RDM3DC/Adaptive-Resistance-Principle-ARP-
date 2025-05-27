"""
realignr_training_runner.py
---------------------------
Generic RealignR/ARP training runner for any PyTorch nn.Module model.
- Supports ARP/Adam optimizers, meta-controllers, full TensorBoard diagnostics.
- Plug in any model, dataset, loss function, and batch size.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
import os
import time
from pathlib import Path

# --- Import your custom modules (add or adapt as needed) ---
from arp_optimizer import ARPOptimizer  # Or use torch.optim.Adam for baseline
from realignr_logging import log_arp_metrics, log_loss_slope, log_spinor_memory




# Meta-Controller, CPRController, and Lyapunov Stability import
from meta_controller import MetaController, CPRController
from lyapunov_stability import LyapunovStabilityVerifier


# ---------------- CONFIGURATION --------------------
config = {
    "experiment_name": "realignr_experiment",
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "log_dir": "runs/realignr_experiment",
    "batch_size": 1024,
    "num_epochs": 500,
    "learning_rate": 0.001,
    "optimizer_type": "Adam",         # "ARP" or "Adam"
    "checkpoint_dir": "checkpoints_realignr",
    "seed": 42,
    "num_workers": 2,
    "max_grad_norm": 5.0,            # For gradient clipping
    "model_save_interval": 50,       # Save checkpoint every 50 epochs
}

# --- Set random seeds for reproducibility ---
torch.manual_seed(config["seed"])
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(config["seed"])

os.makedirs(config["log_dir"], exist_ok=True)
os.makedirs(config["checkpoint_dir"], exist_ok=True)
writer = SummaryWriter(config["log_dir"])



# --- CMAExtractor Example: Feature extractor with curve memory ---
from feature_extractors import CMAExtractor

# --- DataLoader Example (CIFAR-100) ---
import torchvision
import torchvision.transforms as transforms
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])
trainset = torchvision.datasets.CIFAR100(root='./data', train=True, download=True, transform=transform)
testset = torchvision.datasets.CIFAR100(root='./data', train=False, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=config["batch_size"], shuffle=True, num_workers=config["num_workers"])
testloader = torch.utils.data.DataLoader(testset, batch_size=config["batch_size"], shuffle=False, num_workers=config["num_workers"])

# --- Model Setup ---

device = torch.device(config["device"])
model = CMAExtractor(num_classes=100, feature_dim=128).to(device)
if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)
    if __name__ == "__main__":
        print(f"Using {torch.cuda.device_count()} GPUs")

# --- Optimizer ---
if config["optimizer_type"] == "ARP":
    optimizer = ARPOptimizer(model.parameters(), lr=config["learning_rate"])
else:
    optimizer = optim.Adam(model.parameters(), lr=config["learning_rate"])

criterion = nn.CrossEntropyLoss()

# ---------------- TRAINING LOOP ---------------------
def train_and_evaluate():
    # Meta-Controller instantiation
    meta_controller = MetaController()
    cpr = CPRController()
    stability = LyapunovStabilityVerifier()
    global_step = 0
    prev_loss = None

    for epoch in range(config["num_epochs"]):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        epoch_start = time.time()

        for i, (inputs, labels) in enumerate(trainloader):
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()

            # --- Label sanity check for CrossEntropyLoss (batch-wise) ---
            if not torch.all((labels >= 0) & (labels < 100)):
                print("BAD LABELS DETECTED:", labels)
                print("Min/max label:", labels.min().item(), labels.max().item())
                raise ValueError("Label out of range for CrossEntropyLoss!")
            if labels.dtype != torch.long:
                print("Label dtype:", labels.dtype, "-- converting to long.")
                labels = labels.long()

            # --- Forward pass with feature return ---
            outputs, feats = model(inputs, labels, return_feats=True)
            # --- Sanity check output shape ---
            if outputs.shape[0] != labels.shape[0]:
                print(f"Output batch size {outputs.shape[0]} does not match labels {labels.shape[0]}")
                raise ValueError("Output and label batch size mismatch!")
            loss = criterion(outputs, labels)

            # --- Safe curve_memory update (after forward, on main process only, using feats) ---
            if hasattr(model, 'module'):
                cma_model = model.module
            else:
                cma_model = model
            with torch.no_grad():
                feats_cpu = feats.detach().cpu()
                labels_cpu = labels.detach().cpu()
                for i, l in enumerate(labels_cpu):
                    l = int(l.item())
                    if 0 <= l < cma_model.curve_memory.shape[0]:
                        cma_model.curve_memory[l] = 0.9 * cma_model.curve_memory[l] + 0.1 * feats_cpu[i]
            # --- CMA memory logging ---
            from cma_logging import log_cma_memory
            log_cma_memory(writer, model.module if hasattr(model, "module") else model, global_step)
            loss.backward()

            # --- Gradient clipping (optional) ---
            torch.nn.utils.clip_grad_norm_(model.parameters(), config["max_grad_norm"])

            optimizer.step()

            # --- RealignR/ARP logging ---
            if config["optimizer_type"] == "ARP":
                log_arp_metrics(writer, optimizer, global_step)
                if prev_loss is None:
                    prev_loss = loss.item()
                prev_loss = log_loss_slope(writer, loss.item(), prev_loss, global_step)

            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if (i + 1) % 10 == 0:
                train_acc = 100 * correct / total
                avg_loss = running_loss / 10
                print(f"[Epoch {epoch+1}, Batch {i+1}] Loss: {avg_loss:.4f}, Acc: {train_acc:.2f}%")
                writer.add_scalar('Loss/train_batch', avg_loss, global_step)
                writer.add_scalar('Accuracy/train_batch', train_acc, global_step)
                # --- Meta-Controller decision ---
                meta_decision = meta_controller.update(loss.item(), epoch=epoch, accuracy=train_acc)
                if meta_decision == "switch_phase":
                    print("Meta-Controller: Switching phase (e.g., optimizer or feature mode)")
                    # Insert code to switch optimizer, learning rate, or model mode here

                # --- CPR Controller decision ---
                cpr_state = cpr.update(loss.item())
                if cpr_state == "TRIGGERED":
                    print("CPR triggered! Reducing ARP alpha for stabilization.")
                    if config["optimizer_type"] == "ARP":
                        for param_group in optimizer.param_groups:
                            param_group['alpha'] *= 0.7
                elif cpr_state == "RESET":
                    print("CPR reset: restoring ARP alpha.")
                    for param_group in optimizer.param_groups:
                        param_group['alpha'] = config["learning_rate"]
                running_loss = 0.0
                correct = 0
                total = 0
            # --- Lyapunov Stability Diagnostics (every 10 batches) ---
            if (i + 1) % 10 == 0:
                grad_norm = sum((p.grad.norm().item()**2 for p in model.parameters() if p.grad is not None)) ** 0.5
                stability_metrics = stability.check_lyapunov_stability(epoch, model, loss.item(), grad_norm)
                writer.add_scalar('Lyapunov/energy', stability_metrics["energy"], global_step)
                writer.add_scalar('Lyapunov/is_stable', int(stability_metrics["is_stable"]), global_step)
            global_step += 1

        # --- Epoch Checkpoint ---
        if (epoch + 1) % config["model_save_interval"] == 0:
            torch.save(model.state_dict(), os.path.join(config["checkpoint_dir"], f"model_epoch_{epoch+1}.pth"))
            print(f"Checkpoint saved at epoch {epoch+1}")

        # --- Evaluation ---
        model.eval()
        test_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in testloader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                test_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        avg_test_loss = test_loss / len(testloader)
        test_acc = 100 * correct / total
        print(f"Epoch {epoch+1} Test Accuracy: {test_acc:.2f}%, Avg Test Loss: {avg_test_loss:.4f}")
        writer.add_scalar('Loss/test_epoch', avg_test_loss, epoch + 1)
        writer.add_scalar('Accuracy/test_epoch', test_acc, epoch + 1)
        writer.flush()
        print(f"Epoch {epoch+1} took {time.time() - epoch_start:.2f}s")

    print("Training complete. TensorBoard logs at:", config["log_dir"])
    writer.close()

# -------------------- MAIN -------------------------
if __name__ == "__main__":
    train_and_evaluate()

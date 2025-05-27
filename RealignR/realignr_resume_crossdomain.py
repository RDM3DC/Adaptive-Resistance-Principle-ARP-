# ------------------------------------------------------------
# realignr_resume_crossdomain.py — *fresh‑start, long‑haul version*
# ------------------------------------------------------------
#  • Starts from HuggingFace GPT‑2 weights (no checkpoint)
#  • AdamW warm‑up → ARP after N epochs
#  • Dynamic context schedule: 1 024 → 2 048 → 4 096 tokens
#  • Two‑GPU DataParallel (Windows‑friendly, NCCL‑free)
#  • TensorBoard with purge_step=0, auto‑rotating checkpoints
# ------------------------------------------------------------

# ── expose both 3090 Ti GPUs *before* torch import ───────────
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
print("CUDA_VISIBLE_DEVICES =", os.environ["CUDA_VISIBLE_DEVICES"])

# ── std / third‑party ------------------------------------------------
import time
import argparse
import math
import random
from pathlib import Path
from itertools import chain

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import GPT2TokenizerFast
from datasets import load_dataset
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

# ── Gradient Rover Scout ------------------------------------------------
def rover_scout(model, optimizer, batch, tokenizer, step_size=0.001, scout_factor=0.1, 
                curvature_threshold=1.0, device="cuda"):
    """
    Proactive gradient exploration to detect problematic optimization regions.
    
    Args:
        model: The neural network model
        optimizer: The optimizer
        batch: Current batch of data for loss evaluation
        tokenizer: Tokenizer for sequence lengths
        step_size: Base step size (default: 0.001)
        scout_factor: How far ahead to explore (default: 0.1)
        curvature_threshold: Threshold for dangerous curvature changes (default: 1.0)
        device: Computation device (default: "cuda")
        
    Returns:
        dict: Scout metrics including recommendation for step adjustment
    """
    # Save original parameters and requires_grad status.
    # These must be defined *before* the try block whose finally clause uses them.
    try:
        original_params_tuples = [(name, p.clone()) for name, p in model.named_parameters()]
        original_requires_grad_map = {name: p.requires_grad for name, p in model.named_parameters()}
    except Exception as e_init_clone:
        print(f"❌ Critical error in rover_scout during initial parameter cloning: {e_init_clone}")
        return { # Return safe defaults
            "scout_loss": 0.0, "scout_grad_norm": 0.0, "scout_curvature_mean": None,
            "scout_curvature_std": None, "is_dangerous": False, "step_adjustment": 1.0
        }

    # Initialize metrics that will be computed.
    scout_loss_val = 0.0
    scout_grad_norm_val = 0.0
    scout_curvature_mean_val = None
    scout_curvature_std_val = None
    is_dangerous_decision = False
    step_adjustment_factor = 1.0
    error_in_grad_calc = False

    try: # This is the main operational block.
        input_ids = batch["input_ids"].to(device)
        labels = input_ids.clone()

        with torch.no_grad(): # For parameter perturbation and initial loss evaluation.
            # Scout ahead: modify parameters temporarily based on main step's gradients.
            for name, p in model.named_parameters():
                if p.grad is not None: # p.grad is from the main training step's backward pass.
                    p.data.add_(p.grad, alpha=scout_factor * step_size)

            # Evaluate loss at the scouted position.
            logits, _ = model(input_ids)
            scout_loss_val = F.cross_entropy(
                logits[:, :-1, :].reshape(-1, tokenizer.vocab_size),
                labels[:, 1:].reshape(-1)
            ).item()

            # Compute curvature metrics if the model supports it.
            core_model = model.module if isinstance(model, torch.nn.DataParallel) else model
            if hasattr(core_model, 'C'):
                scout_curvature_mean_val = core_model.C.mean().item()
                scout_curvature_std_val = core_model.C.std().item()
            
            # Calculate gradients at this new scouted position.
            model.zero_grad() # Clear any old gradients.
            
            with torch.enable_grad(): # Enable gradient computation for this block.
                # Ensure parameters that should be trainable have requires_grad set.
                for name, param in model.named_parameters():
                    if original_requires_grad_map.get(name, False): # If it was originally trainable.
                        param.requires_grad_(True)
                    else: # If not originally trainable, ensure it remains so.
                        param.requires_grad_(False)
                
                try:
                    # print(f"🔍 Rover scout: Performing backward pass at scouted position.")
                    logits_for_grad, _ = model(input_ids) # Forward pass.
                    loss_at_scout_for_grad = F.cross_entropy(
                        logits_for_grad[:, :-1, :].reshape(-1, tokenizer.vocab_size),
                        labels[:, 1:].reshape(-1)
                    )
                    loss_at_scout_for_grad.backward() # Compute gradients.

                    # Calculate the norm of these new gradients.
                    current_grad_norm_sq = 0.0
                    for name, p in model.named_parameters():
                        if p.grad is not None and original_requires_grad_map.get(name, False):
                            current_grad_norm_sq += p.grad.norm().item() ** 2
                    scout_grad_norm_val = current_grad_norm_sq ** 0.5
                
                except RuntimeError as e_rt_grad:
                    print(f"❌ RuntimeError during rover scout's gradient calculation: {e_rt_grad}")
                    error_in_grad_calc = True # Flag the error.
                except Exception as e_other_grad:
                    print(f"❌ Unexpected error during rover scout's gradient calculation: {e_other_grad}")
                    error_in_grad_calc = True # Flag the error.
        
        # Decision making based on scout results.
        if not error_in_grad_calc: 
            if scout_curvature_mean_val is not None and scout_curvature_std_val is not None:
                curvature_variation = scout_curvature_std_val / max(scout_curvature_mean_val, 1e-6)
                if curvature_variation > curvature_threshold:
                    is_dangerous_decision = True
                    step_adjustment_factor = 0.5
            
            if scout_grad_norm_val > 10.0: 
                is_dangerous_decision = True
                step_adjustment_factor = min(step_adjustment_factor, 0.3)
        # else: # If grad calculation failed, current metrics (grad_norm=0) will be used.

    finally: # This `finally` block ensures parameter restoration.
        # Restore all parameters to their original data and requires_grad state.
        for name, original_data_tensor in original_params_tuples:
            try:
                # Efficiently get parameter by name
                param_to_restore = dict(model.named_parameters()).get(name)
                if param_to_restore is not None:
                    param_to_restore.data.copy_(original_data_tensor)
                    param_to_restore.requires_grad_(original_requires_grad_map.get(name, False))
                # else:
                    # print(f"⚠️ Rover Scout: Parameter '{name}' not found during restoration.")
            except Exception as e_restore:
                print(f"❌ Error restoring parameter '{name}' in rover_scout finally: {e_restore}")
        
        model.zero_grad(set_to_none=True) # Clean up .grad attributes from rover's backward pass.

    return {
        "scout_loss": scout_loss_val,
        "scout_grad_norm": scout_grad_norm_val,
        "scout_curvature_mean": scout_curvature_mean_val,
        "scout_curvature_std": scout_curvature_std_val,
        "is_dangerous": is_dangerous_decision,
        "step_adjustment": step_adjustment_factor
    }

# ── local utilities --------------------------------------------------
from optimizers.arp_optimizer import ARPOptimizer
from meta_controller import MetaController, CPRController
from action import ActionTracker
from dataset_scheduler import DatasetScheduler  # Import our new dataset scheduler
from enhanced_cpr_controller import EnhancedCPRController
from explicit_jacobian import ExplicitJacobian  # Import explicit Jacobian module
from lyapunov_stability import LyapunovStabilityVerifier  # Import Lyapunov stability verifier
# Import memory retention system
from memory_retention import MemoryRetention

# Parse command-line arguments for starting step and checkpoint resume path
parser = argparse.ArgumentParser(description="Train RealignR GPT-2 crossdomain")
parser.add_argument('-s', '--start', type=int, default=0, help='Step to start from')
parser.add_argument('-c', '--checkpoint', type=str, default=None, help='Path to checkpoint to resume from')
args = parser.parse_args()

# ── CONSTANTS --------------------------------------------------------
CURVATURE_MIN_THRESHOLD = 0.15  # Threshold for C_ij.mean()
DELTA = 0.01        # Initial curvature learning rate
EPSILON = 0.001     # Initial curvature memory decay rate
L_MAX = 10.0        # Reference loss or path-length measure
BASE_DIR   = Path(__file__).resolve().parent
STEP_START = args.start  # Start from provided step
LOG_DIR    = BASE_DIR / "runs" / f"realignr_crossdomain_{int(time.time())}"
CKPT_DIR   = BASE_DIR / "checkpoints" # Checkpoints are in the checkpoints folder
RESUME_CKPT = Path(args.checkpoint) if args.checkpoint else None  # Checkpoint path if provided
ROVER_RESTORE_STEPS = 200  # Steps before restoring learning rate after rover adjustment

# Dataset switching schedule file (JSON)
DATASET_SCHEDULE = BASE_DIR / "dataset_schedule.json"

MAX_STEPS  = 300_000
CKPT_INTERVAL = 2_000
LOG_INTERVAL  = 50
MAX_BACKUPS   = 8

SEQ_LEN   = 1_024 # Keep for data processing functions
CTX_START = 1_024 # Start model with this context length (start small, expand later)
BATCH_SIZE = 4
CONTEXT_SCHEDULE = [
    (50_000, 2_048),   # Expand to 2k at step 50k
    (120_000, 4_096),  # Expand to 4k at step 120k
]
ALPHA, MU = 0.01, 0.001
# ARP_SWITCH_EPOCHS = 20 # No longer needed

GEN_PROMPT = "The meaning of life is"
GEN_LEN    = 50

os.makedirs(LOG_DIR, exist_ok=True)
# os.makedirs(CKPT_DIR, exist_ok=True) # No need to create BASE_DIR

# ── TOKENIZER / DATA HELPERS ----------------------------------------
# Uses SEQ_LEN for padding/chunking
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2"); tokenizer.pad_token = tokenizer.eos_token

def encode_batch(text_list):
    # Uses SEQ_LEN
    enc = tokenizer(text_list, padding="max_length", truncation=True,
                    max_length=SEQ_LEN, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]

def tokenize_and_chunk(ex):
    ids = tokenizer(ex["text"], add_special_tokens=False)["input_ids"]
    flat = list(chain.from_iterable(ids))
    # Uses SEQ_LEN
    return {"input_ids": [flat[i:i+SEQ_LEN] for i in range(0, len(flat), SEQ_LEN)]}

def get_packed_wikitext103(split="train[:2%]"):
    ds = load_dataset("wikitext", "wikitext-103-raw-v1", split=split)
    ds = ds.map(tokenize_and_chunk, batched=True, remove_columns=["text"])
    # Uses SEQ_LEN
    ds = ds.filter(lambda e: len(e["input_ids"]) == SEQ_LEN).with_format("torch")
    return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=split.startswith("train"))

# ── MODEL ------------------------------------------------------------
class Block(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.ff   = nn.Sequential(nn.Linear(dim, dim*4), nn.GELU(), nn.Linear(dim*4, dim))
        self.ln1, self.ln2 = nn.LayerNorm(dim), nn.LayerNorm(dim)
    def forward(self, x, mask):
        # attention + residual + layernorm
        a, _ = self.attn(x, x, x, attn_mask=mask)
        x = self.ln1(x + a)
        # feed-forward + residual + layernorm
        x = self.ln2(x + self.ff(x))
        # cache output for EMA-based G update
        self.last_out = x.detach()
        return x

class RealignRGPT2(nn.Module):
    # Accept ctx_len explicitly
    def __init__(self, vocab, ctx_len):
        super().__init__()
        dim = 768
        self.ctx_len  = ctx_len # Use provided ctx_len
        self.tok_emb  = nn.Embedding(vocab, dim)
        # Initialize pos_emb with the provided ctx_len
        self.pos_emb  = nn.Parameter(torch.zeros(1, ctx_len, dim))
        self.blocks   = nn.ModuleList(Block(dim, 12) for _ in range(4))
        self.ln_f     = nn.LayerNorm(dim)
        self.head     = nn.Linear(dim, vocab, bias=False)

        # Initialize G as a tensor with dimensions [n_blocks, d_model]
        g_init = torch.zeros(len(self.blocks), dim)
        self.register_buffer("G", g_init)
        # Initialize C (curvature memory) as all ones
        c_init = torch.ones(len(self.blocks), dim)
        self.register_buffer("C", c_init)

    def expand_ctx(self, new_len):
        if new_len <= self.ctx_len: return
        old = self.pos_emb.data; new = torch.zeros(1, new_len, old.size(2), device=old.device)
        new[:, :self.ctx_len] = old; nn.init.trunc_normal_(new[:, self.ctx_len:], std=0.02)
        self.pos_emb, self.ctx_len = nn.Parameter(new), new_len
        print(f"🔁 context window → {new_len}")
    def forward(self, idx):
        B,T = idx.shape
        x = self.tok_emb(idx) + self.pos_emb[:, :T]
        mask = torch.triu(torch.ones(T,T,device=idx.device)*float('-inf'), 1)

        activ_mean = []                              # collect |x| mean per block
        for blk in self.blocks:
            x = blk(x,mask)
            activ_mean.append(x.abs().mean((0, 1)))  # (d_model,)

        return self.head(self.ln_f(x)), activ_mean   # return per-block stats

    @torch.no_grad()
    def generate(self, prompt, max_len=GEN_LEN, temp=1.0, top_k=0):
        self.eval(); ids = tokenizer.encode(prompt, return_tensors="pt").to(self.head.weight.device)
        for _ in range(max_len):
            logits,_ = self(ids[:, -self.ctx_len:]); logits = logits[:,-1,:]/temp
            if top_k:
                topv, topi = torch.topk(logits, top_k)
                logits = torch.full_like(logits, -float('inf')); logits.scatter_(1, topi, topv)
            next_tok = torch.multinomial(torch.softmax(logits,-1), 1); ids = torch.cat([ids,next_tok],-1)
        return tokenizer.decode(ids[0], skip_special_tokens=True)

# ── BUILD MODEL ----------------------------------------------
"""Initialize model with the context length matching the checkpoint"""
# Check if CUDA is available
if torch.cuda.is_available():
    base_model = RealignRGPT2(tokenizer.vocab_size, ctx_len=CTX_START).cuda()
    model = torch.nn.DataParallel(base_model, device_ids=[0,1]); core = model.module
    print(f"Using GPU - DataParallel devices: {model.device_ids} | torch sees {torch.cuda.device_count()} GPUs")
else:
    print("CUDA not available! Falling back to CPU (this will be very slow)")
    base_model = RealignRGPT2(tokenizer.vocab_size, ctx_len=CTX_START)
    model = base_model; core = model  # No DataParallel for CPU mode
print("DataParallel devices:", model.device_ids, "| torch sees", torch.cuda.device_count(), "GPUs")
print(f"Model initialized with context length: {core.ctx_len}")

# Debug: Check G shape
print(f"G shape: {core.G.shape}") # Should be torch.Size([4, 768])

# ── DEFINE OPTIMISER (Starting directly with ARP) --------------------------
optimizer = ARPOptimizer(model.parameters(), alpha=ALPHA, mu=MU)
print(f"🔀 Resuming with ARP (α={ALPHA}, μ={MU}) from step {STEP_START}")

# ── RESUME FROM CHECKPOINT ----------------------------------------------
step = STEP_START # Initialize step with STEP_START
print("🚀 Starting fresh training run from scratch.")
print("First token weights L2:", core.tok_emb.weight[0].norm().item())

# ── CONTROLLERS ------------------------------------------------------

# Initialize the enhanced CPR controller with curvature monitoring
cpr = EnhancedCPRController(
    epsilon=1e-3,
    reset_patience=500,
    loss_window_size=100,
    loss_spike_threshold=1.2,
    curv_spike_threshold=1.5,
    adaptive_patience=True,
    use_curvature_signals=True
)
meta = MetaController()
action_tracker = ActionTracker(λ1=0.15)

# Initialize explicit Jacobian calculator (for periodic validation)
jacobian_calc = ExplicitJacobian(device="cuda")

# Initialize Lyapunov stability verifier
stability_verifier = LyapunovStabilityVerifier(
    history_length=100,
    check_interval=2000,
    stability_threshold=0.6,
    energy_function_type='quadratic'
)

# ── DATASET SCHEDULER -----------------------------------------------
# Replace simple loader with cross-domain dataset scheduler
# Create memory snapshots directory
MEMORY_DIR = LOG_DIR / "memory_snapshots"
MEMORY_DIR.mkdir(exist_ok=True)

# Initialize dataset scheduler with memory retention capabilities
dataset_scheduler = DatasetScheduler(
    tokenizer=tokenizer,
    batch_size=BATCH_SIZE,
    schedule_path=DATASET_SCHEDULE if Path(DATASET_SCHEDULE).exists() else None,
    seq_len=SEQ_LEN,
    memory_snapshots_dir=MEMORY_DIR,
    memory_adaptation_rate=0.8  # 80% retain current, 20% from previous domain
)
print(f"📚 Enhanced dataset scheduler initialized with memory retention")

# ── LOGGER -----------------------------------------------------------
writer = SummaryWriter(str(LOG_DIR), purge_step=STEP_START) # Use STEP_START for purge_step
print(f"▶️  Training starts/resumes at step {step}, ctx={core.ctx_len}") # Use loaded/updated step
print(f"[TensorBoard] Log directory: {LOG_DIR}")
print(f"[TensorBoard] Run: tensorboard --logdir \"{LOG_DIR}\"")

# ── CHECKPOINT HELPER -----------------------------------------------
def save_ckpt(step:int):
    # Save checkpoints to CKPT_DIR with unique timestamped names
    fn = CKPT_DIR / f"gpt2_s0_step{step}_{int(time.time())}.pth"
    torch.save({"model_state_dict": core.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "step": step}, fn)
    # Only delete old checkpoints in CKPT_DIR, not globally
    old = sorted(CKPT_DIR.glob("gpt2_s0_step*.pth"))[:-MAX_BACKUPS]
    for f in old: f.unlink(missing_ok=True)
    print(f"💾 checkpoint saved @ {step} → {fn}")

# ── TRAIN LOOP -------------------------------------------------------
ema = None; ctx_idx = 0 # step is now loaded or set above
# Remove the pre-loop context expansion logic as model starts with correct ctx_len
# The loop's dynamic expansion logic will handle future increases based on CONTEXT_SCHEDULE
print(f"Initial context index set to {ctx_idx} (no pre-expansion needed)")

last_curv_warn_step = -100  # For throttling curvature mean warnings
rover_adjusted_step = -1    # Track last step when rover adjusted learning rate
original_alpha = ALPHA      # Keep original learning rate for restoration

while step < MAX_STEPS:    # -- Curvature logging and anomaly detection --

    # -- Curvature memory C logging and analysis --
    writer.add_scalar('Curvature/C_mean', core.C.mean().item(), step)
    writer.add_scalar('Curvature/C_std', core.C.std().item(), step)
    writer.add_histogram('Curvature/C_hist', core.C, step)
    
    # Log per-block curvature statistics
    for k in range(core.C.size(0)):
        writer.add_scalar(f'Curvature/C_block{k}_mean', core.C[k].mean().item(), step)
        writer.add_scalar(f'Curvature/C_block{k}_std', core.C[k].std().item(), step)
    
    # Dynamic adaptation of curvature parameters based on statistics
    c_mean = core.C.mean().item()
    c_std = core.C.std().item()
    c_var_ratio = c_std / max(c_mean, 1e-6)  # Variance-to-mean ratio
    
    # 1. Monitor for anomalies and log warnings
    C_mean_high_threshold = 2.0
    C_mean_low_threshold = CURVATURE_MIN_THRESHOLD
    C_variance_high_threshold = 0.5  # std/mean ratio
    
    if c_mean > C_mean_high_threshold:
        if step - last_curv_warn_step >= 100:  # Throttle warnings
            print(f"⚠️ Curvature mean high at step {step}: {c_mean:.4f}")
            last_curv_warn_step = step
    
    # 2. Dynamic DELTA adjustment based on curvature mean    if c_mean < C_mean_low_threshold:
        # Increase learning rate if curvature is too low
        DELTA *= 1.05
        writer.add_scalar('Curvature/DELTA_adjust_up', DELTA, step)
        if step % LOG_INTERVAL == 0:
            print(f"📝 Increasing curvature learning rate δ to {DELTA:.6f} at step {step}")
    elif c_mean > C_mean_high_threshold * 1.5:
        # Decrease learning rate if curvature is excessively high
        DELTA *= 0.95
        writer.add_scalar('Curvature/DELTA_adjust_down', DELTA, step)
        if step % LOG_INTERVAL == 0:
            print(f"📝 Decreasing curvature learning rate δ to {DELTA:.6f} at step {step}")
    
    # 3. Dynamic EPSILON adjustment based on curvature variance ratio    if c_var_ratio > C_variance_high_threshold:
        # Reduce decay rate when variance is high to stabilize
        EPSILON *= 0.95
        writer.add_scalar('Curvature/EPSILON_adjust_down', EPSILON, step)
        if step % LOG_INTERVAL == 0:
            print(f"📝 Reducing curvature decay ε to {EPSILON:.6f} at step {step} (variance: {c_var_ratio:.4f})")
    elif c_var_ratio < C_variance_high_threshold * 0.5 and c_mean > C_mean_low_threshold * 2:
        # Increase decay rate when variance is low and mean is healthy
        EPSILON *= 1.02
        writer.add_scalar('Curvature/EPSILON_adjust_up', EPSILON, step)
        if step % LOG_INTERVAL == 0:
            print(f"📝 Increasing curvature decay ε to {EPSILON:.6f} at step {step} (variance: {c_var_ratio:.4f})")
    
    # Log current values of adaptation parameters
    writer.add_scalar('Curvature/DELTA', DELTA, step)
    writer.add_scalar('Curvature/EPSILON', EPSILON, step)
    writer.add_scalar('Curvature/variance_ratio', c_var_ratio, step)
    
    # dynamic ctx expansion (handles increases > CTX_START)
    if ctx_idx < len(CONTEXT_SCHEDULE) and step >= CONTEXT_SCHEDULE[ctx_idx][0]:
        target_ctx = CONTEXT_SCHEDULE[ctx_idx][1]
        if target_ctx > core.ctx_len:
            print(f"🔁 Expanding context window: {core.ctx_len} → {target_ctx} at step {step}")
            core.expand_ctx(target_ctx)
        else:
            print(f"Skipping context schedule entry {CONTEXT_SCHEDULE[ctx_idx]} as target length is not greater than current {core.ctx_len}")
        ctx_idx += 1    # Check for dataset switching based on schedule, passing the model core
    # This will automatically handle memory snapshots and adaptation
    if dataset_scheduler.check_schedule(step, core):
        print(f"🔄 Dataset switched at step {step} with memory adaptation")
        writer.add_scalar('Training/dataset_switch', 1.0, step)
        
        # Generate visualization of memory transitions so far
        if len(dataset_scheduler.memory_retention.snapshots) > 1:
            try:
                viz_path = dataset_scheduler.visualize_memory_transitions(
                    save_path=MEMORY_DIR / f"transitions_{step}.png"
                )
                print(f"📊 Memory transition visualization saved to {viz_path}")
            except Exception as e:
                print(f"Warning: Could not create memory transition visualization - {e}")

    # Get next batch from dataset scheduler
    batch = dataset_scheduler.get_next_batch()
    input_ids = batch["input_ids"].cuda()
    labels = input_ids.clone()
    
    # Forward pass 
    logits, activ_mean = model(input_ids)  # Capture activation means
    
    # Loss calculation
    loss = F.cross_entropy(
        logits[:, :-1, :].reshape(-1, tokenizer.vocab_size),
        labels[:, 1:].reshape(-1)
    )
      # Periodic Jacobian verification (every 5000 steps)
    if step > 0 and step % 5000 == 0:
        print(f"⚙️ Verifying gradient calculation accuracy at step {step}...")
        accuracy_metrics = jacobian_calc.verify_autograd_accuracy(model, input_ids, labels)
        avg_error = sum(accuracy_metrics.values()) / len(accuracy_metrics)
        writer.add_scalar('Gradient/autograd_accuracy', 1.0 - min(avg_error, 1.0), step)
        
        if avg_error > 0.1:  # If error is significant
            print(f"⚠️ Gradient calculation discrepancy detected: {avg_error:.4f} relative error")
            print(f"📝 Significant gradient discrepancy: {avg_error:.4f} at step {step}")
      # Optimization step with optional Jacobian preconditioner
    optimizer.zero_grad()
    loss.backward()
    
    # Apply Jacobian preconditioner on rare occasions (every 10000 steps)
    if step > 0 and step % 10000 == 0 and isinstance(optimizer, ARPOptimizer):
        jacobian_calc.apply_jacobian_preconditioner(optimizer, model, input_ids, labels, alpha=0.05)
        print(f"🧠 Applied Jacobian preconditioner at step {step}")
    
    # Run gradient rover scout every 1000 steps or when loss spikes
    rover_active = step % 1000 == 0 or (step > 0 and loss.item() > 1.5 * ema)
    step_adjustment = 1.0
    
    if rover_active and isinstance(optimizer, ARPOptimizer):
        rover_results = rover_scout(
            model, 
            optimizer, 
            batch, 
            tokenizer,
            step_size=ALPHA,
            scout_factor=0.2,
            curvature_threshold=0.8,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        
        # Log rover metrics
        writer.add_scalar("Rover/scout_loss", rover_results["scout_loss"], step)
        writer.add_scalar("Rover/scout_grad_norm", rover_results["scout_grad_norm"], step)
        
        if rover_results["scout_curvature_mean"] is not None:
            writer.add_scalar("Rover/scout_curvature_mean", rover_results["scout_curvature_mean"], step)
            writer.add_scalar("Rover/scout_curvature_std", rover_results["scout_curvature_std"], step)
        
        # Apply step size adjustment if dangerous terrain detected
        step_adjustment = rover_results["step_adjustment"]
        if rover_results["is_dangerous"]:
            print(f"⚠️ Rover scout detected dangerous terrain at step {step}. Adjusting step size.")
            writer.add_scalar("Rover/danger_detected", 1.0, step)
              # Temporarily adjust optimizer's learning rate
            for param_group in optimizer.param_groups:
                param_group['alpha'] *= step_adjustment
            
            writer.add_scalar("Rover/step_adjustment", step_adjustment, step)
            rover_adjusted_step = step  # Record that we adjusted the learning rate
      # Take the (potentially adjusted) optimization step
    optimizer.step()
    
    # Check if we need to restore learning rate after a rover adjustment
    if rover_adjusted_step > 0 and step - rover_adjusted_step >= ROVER_RESTORE_STEPS:
        if isinstance(optimizer, ARPOptimizer):
            for param_group in optimizer.param_groups:
                param_group['alpha'] = original_alpha
            writer.add_scalar("Rover/lr_restored", original_alpha, step)
            print(f"🔄 Restoring learning rate to {original_alpha} at step {step}")
            rover_adjusted_step = -1  # Reset flag
    # -- EMA-based G update (block-wise exponential moving average, with curvature) ----------
    if isinstance(optimizer, ARPOptimizer):
        with torch.no_grad():
            # activ_mean is a list of per-block activation stats (possibly stacked across GPUs)
            for b, act_stat in enumerate(activ_mean):
                # act_stat may be shape (num_replicas, d_model) or (d_model,)
                # compute scalar mean over all elements
                act_abs_mean = act_stat.mean()
                # EMA update: decay by (1-MU), then add ALPHA * act_abs_mean * C[b]
                core.G[b] = core.G[b] * (1 - MU) + ALPHA * act_abs_mean * core.C[b]
        # -- ACP curvature memory update (after G update)
        with torch.no_grad():
            # Apply the discovered adaptive geometry equation for curvature memory updates:
            # C_new = C_old + DELTA × (L_max - Loss)^(2 - Loss/L_max) - EPSILON × C_old
            gamma = 2.0 - (loss.item() / L_MAX)
            base = max(L_MAX - loss.item(), 0.0)
            curvature_update = DELTA * (base ** gamma) - EPSILON * core.C
            
            # Apply update to curvature memory
            core.C += curvature_update
            
            # Ensure curvature values remain positive with reasonable lower bound
            core.C = torch.clamp(core.C, min=0.1)  # Keep C positive and stable    # -- Enhanced CPR diagnostics --------------------------------
    # Pass both loss and curvature values to CPR controller
    c_mean = core.C.mean().item() if hasattr(core, 'C') else None
    state = cpr.update(loss.item(), curvature=c_mean)
    
    # Handle different CPR states
    if state == "TRIGGERED":
        if step % 100 == 0:  # Throttle trigger messages
            print(f"⚠️ CPR trigger at step {step} (loss: {loss.item():.4f}, curvature mean: {c_mean:.4f})")
        writer.add_scalar("CPR/trigger", 1, step)
        
        # Log CPR trigger details
        cpr_stats = cpr.get_stats()
        writer.add_scalar("CPR/trigger_count", cpr_stats["total_triggers"], step)
        writer.add_scalar("CPR/current_trigger_streak", cpr_stats["current_trigger_count"], step)
        writer.add_scalar("CPR/ema_loss", cpr_stats["ema_loss"], step)
        
    elif state == "RESET":
        print(f"🟢 CPR reset at step {step} - stabilizing training")
        writer.add_scalar("CPR/reset", 1, step)
        writer.add_scalar("CPR/total_resets", cpr.get_stats()["total_resets"], step)
        
        # Take adaptive actions on reset
        if isinstance(optimizer, ARPOptimizer):
            # Temporarily reduce learning rates to stabilize
            for param_group in optimizer.param_groups:
                param_group['alpha'] *= 0.8  # Temporarily reduce alpha
                writer.add_scalar("CPR/alpha_adjusted", param_group['alpha'], step)
            
            print(f"📉 Temporarily reducing alpha to stabilize training")
            
            # Schedule alpha restoration after 500 steps
            # This would need to be handled in the training loop

    # -- EMA & logging ----------------------------------
    ema = loss.item() if ema is None else 0.99*ema + 0.01*loss.item()
    
    # Calculate gradient norm for stability verification (if needed)
    grad_norm = None
    if step % 100 == 0:  # Calculate periodically to save computation
        grad_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                grad_norm += p.grad.norm().item() ** 2
        grad_norm = grad_norm ** 0.5
        writer.add_scalar("Gradient/norm", grad_norm, step)
    
    # Perform Lyapunov stability check
    if step >= 1000:  # Start checking after warm-up period
        stability_results = stability_verifier.check_lyapunov_stability(
            step, model, loss.item(), grad_norm
        )
        
        # Log stability metrics
        writer.add_scalar("Stability/energy", stability_results["energy"], step)
        writer.add_scalar("Stability/param_change", stability_results["param_change"], step)
        writer.add_scalar("Stability/score", stability_results.get("stability_score", 0), step)
        
        # Full stability check logs
        if step - stability_verifier.last_check_step == 0:  # Just performed full check
            writer.add_scalar("Stability/is_stable", 1 if stability_results["is_stable"] else 0, step)
            
            if "energy_decreasing" in stability_results and stability_results["energy_decreasing"] is not None:
                writer.add_scalar("Stability/energy_decreasing", 
                                 1 if stability_results["energy_decreasing"] else 0, step)
            
            # Generate and save stability plot every 10K steps
            if step % 10000 == 0:
                try:
                    plot_path = stability_verifier.save_stability_plot(Path(LOG_DIR) / "stability_plots", step)
                    print(f"📊 Stability analysis plot saved to {plot_path}")
                except Exception as e:
                    print(f"Warning: Could not save stability plot - {e}")
            
            # Log stability status
            if stability_results["is_stable"]:
                print(f"🟢 System is Lyapunov stable at step {step} (score: {stability_results['stability_score']:.2f})")
            else:
                print(f"🟠 System not yet Lyapunov stable at step {step} (score: {stability_results['stability_score']:.2f})")
    
    if step % LOG_INTERVAL == 0:
        writer.add_scalar("Loss/train", loss.item(), step)
        writer.add_scalar("Loss/train_smooth", ema, step)
        writer.add_scalar("ctx_len", core.ctx_len, step)
        writer.flush()  # Explicit flush to ensure event file is updated
        print(f"step {step} | loss {loss:.4f} | ema {ema:.4f} | ctx {core.ctx_len}")    # -- TensorBoard G logging (optional) ----------------
    if step % 1000 == 0:
        writer.add_histogram("G/hist_all", core.G, step)
    for k in range(core.G.size(0)):
        writer.add_scalar(f"G_block{k}/mean", core.G[k].mean().item(), step)
        writer.add_scalar(f"G_block{k}/std", core.G[k].std().item(), step)

    # -- checkpoints ------------------------------------
    if step and step % CKPT_INTERVAL == 0:
        save_ckpt(step)
        writer.add_text("Sample", core.generate(GEN_PROMPT, temp=0.8, top_k=50), step)

    step += 1

print("🎉 training loop finished")
print("Logging to:", LOG_DIR)
writer.flush()
writer.close()
print("✅ TensorBoard logs flushed and closed")

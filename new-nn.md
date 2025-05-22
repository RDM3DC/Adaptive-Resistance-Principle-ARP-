import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report
from sklearn.decomposition import PCA

class CMADeformationLayer(nn.Module):
    def __init__(self, curve_dim, memory_dim, control_dim, hidden_dim, output_points, memory_decay=0.9, memory_reinforcement=0.1):
        super().__init__()
        self.curve_dim = curve_dim
        self.memory_dim = memory_dim
        self.control_dim = control_dim
        self.hidden_dim = hidden_dim
        self.output_points = output_points
        self.memory_decay = memory_decay
        self.memory_reinforcement = memory_reinforcement

        self.curve_encoder = nn.Sequential(
            nn.Linear(output_points * curve_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.fusion_layer = nn.Sequential(
            nn.Linear(hidden_dim + memory_dim + control_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.output_layer = nn.Linear(hidden_dim, output_points * curve_dim)
        self.memory_updater = nn.Linear(output_points * curve_dim, memory_dim)

    def forward(self, curve_input, memory_input, control_input, noise_std=0.0):
        batch_size = curve_input.size(0)
        curve_flat = curve_input.view(batch_size, -1)
        if noise_std > 0:
            curve_flat += torch.randn_like(curve_flat) * noise_std

        curve_features = self.curve_encoder(curve_flat)
        fusion_input = torch.cat([curve_features, memory_input, control_input], dim=-1)
        fused = self.fusion_layer(fusion_input)
        deformation = self.output_layer(fused)
        next_curve = deformation.view(batch_size, self.output_points, self.curve_dim)

        delta_memory = self.memory_updater(curve_flat)
        new_memory = self.memory_decay * memory_input + self.memory_reinforcement * delta_memory
        return next_curve, new_memory

def generate_circle_tensor(batch_size, radius=1.0, points=20):
    t = torch.linspace(0, 2 * torch.pi, points)
    x = radius * torch.cos(t)
    y = radius * torch.sin(t)
    curve = torch.stack([x, y], dim=1).unsqueeze(0).repeat(batch_size, 1, 1)
    return curve

def visualize_curves(curves, title="CMA Output Curves", save_path=None):
    curves = curves.cpu().detach().numpy()
    plt.figure(figsize=(6, 6))
    for i, curve in enumerate(curves[:8]):
        x, y = curve[:, 0], curve[:, 1]
        plt.plot(x, y, label=f"Sample {i}")
    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis('equal')
    plt.grid(True)
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.legend()
        plt.show()

def plot_memory_stats(memory_log, save_path=None):
    memory_log = torch.stack(memory_log).detach().cpu().numpy()
    plt.figure(figsize=(10, 4))
    for i in range(memory_log.shape[1]):
        plt.plot(memory_log[:, i], label=f"Memory[{i}]")
    plt.title("Memory Evolution Over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("Memory Value")
    plt.legend()
    plt.grid(True)
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def plot_memory_pca(memories, labels, save_path=None):
    pca = PCA(n_components=2)
    reduced = pca.fit_transform(memories)
    plt.figure(figsize=(6, 5))
    for label in np.unique(labels):
        idx = labels == label
        plt.scatter(reduced[idx, 0], reduced[idx, 1], label=f"Class {label}", alpha=0.5)
    plt.title("PCA of Memory Representations")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.legend()
    plt.grid(True)
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def train_memory_classifier(memories, labels):
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    clf.fit(memories, labels)
    preds = clf.predict(memories)
    print("\nMemory Symbol Classification Report:")
    print(classification_report(labels, preds))
    plot_memory_pca(memories, labels, save_path="visual_logs/memory_pca.png")

def train_cma_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CMADeformationLayer(curve_dim=2, memory_dim=4, control_dim=3, hidden_dim=128, output_points=20).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    batch_size = 8192
    epochs = 10000
    output_points = 20

    os.makedirs("visual_logs", exist_ok=True)
    memory_log = []
    all_memories = []
    all_labels = []

    symbolic_controls = {
        0: torch.tensor([1.0, 0.0, 0.0]),
        1: torch.tensor([0.0, 1.0, 0.0]),
        2: torch.tensor([0.0, 0.0, 1.0])
    }

    for epoch in range(epochs):
        model.train()
        base_curves = generate_circle_tensor(batch_size, radius=1.0, points=output_points).to(device)
        memory = torch.zeros(batch_size, 4).to(device)

        label_ids = torch.arange(0, batch_size) % 3
        control = torch.stack([symbolic_controls[int(i)] for i in label_ids]).to(device)
        weights = torch.tensor([[2.0, 0.0], [0.0, 2.0], [1.0, -1.0]], device=device)
        target_curves = base_curves + 0.3 * torch.tanh(control.unsqueeze(1) @ weights)

        output, updated_memory = model(base_curves, memory, control)
        loss = criterion(output, target_curves)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

        if (epoch + 1) % 500 == 0:
            torch.save(model.state_dict(), f"cma_model_epoch_{epoch+1}.pt")
            visualize_curves(output[:8], title=f"Epoch {epoch+1} Output", save_path=f"visual_logs/epoch_{epoch+1}.png")
            mean_memory = updated_memory.mean(dim=0)
            memory_log.append(mean_memory)
            print(f"Saved checkpoint and plot at epoch {epoch+1}")

        all_memories.append(updated_memory.detach().cpu())
        all_labels.append(label_ids.cpu())

    torch.save(model.state_dict(), "cma_model_final.pt")
    plot_memory_stats(memory_log, save_path="visual_logs/memory_evolution.png")
    print("Final model saved. Memory evolution plot saved.")

    all_memories = torch.cat(all_memories, dim=0).numpy()
    all_labels = torch.cat(all_labels, dim=0).numpy()
    train_memory_classifier(all_memories, all_labels)
    return model

if __name__ == "__main__":
    print("Training CMADeformationLayer on synthetic symbolic dataset...")
    trained_model = train_cma_model()
    print("Training complete. Model ready for symbolic deformation tasks.")

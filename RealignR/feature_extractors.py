# Ensure nn is imported before DeeperFeatureExtractor
import torch.nn as nn
# Deeper feature extractor for CIFAR-100
class DeeperFeatureExtractor(nn.Module):
    def __init__(self, out_dim=128):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.conv3 = nn.Conv2d(128, 256, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(256)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(256 * 4 * 4, out_dim)
        self.fc2 = nn.Linear(out_dim, out_dim)
    def forward(self, x):
        x = self.pool(torch.relu(self.bn1(self.conv1(x))))  # 16x16
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))  # 8x8
        x = self.pool(torch.relu(self.bn3(self.conv3(x))))  # 4x4
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        return torch.relu(self.fc2(x))
import torch
import torch.nn as nn
import torch.nn.functional as F

# CNN feature extractor
class CNNFeatureExtractor(nn.Module):
    def __init__(self):
        super(CNNFeatureExtractor, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(128 * 4 * 4, 512)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(512, 5)  # 5D for Cl(5)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = x.view(-1, 128 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# Feature extractors for GNC model

class CNNExtractor:
    # ... (CNN feature extractor code will go here)
    pass


class CMAExtractor(nn.Module):
    def __init__(self, num_classes=100, feature_dim=128):
        super().__init__()
        self.feature_dim = feature_dim
        self.feature_extractor = DeeperFeatureExtractor(out_dim=feature_dim)
        self.classifier = nn.Linear(feature_dim, num_classes)
        self.curve_memory = torch.zeros(num_classes, feature_dim)
    def forward(self, x, labels=None, return_feats=False):
        feats = self.feature_extractor(x)
        # Update memory *before* classifier, with feats shape [feature_dim] (optional, now done outside)
        logits = self.classifier(feats)
        if return_feats:
            return logits, feats
        else:
            return logits


class AdaptivePiExtractor(nn.Module):
    def __init__(self, num_classes=100, out_dim=5):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2, 2)
        )
        self.fc = nn.Linear(32 * 16 * 16, out_dim)
        self.pi_values = nn.Parameter(torch.ones(num_classes, out_dim))
    def forward(self, x, labels=None):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        feats = self.fc(x)
        # Apply per-class adaptive pi encoding if labels provided
        if labels is not None:
            feats = feats * self.pi_values[labels]
        return feats

import torch
import torch.nn as nn
import timm

class FrequencyBranch(nn.Module):
    def __init__(self, output_dim: int = 256):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.GELU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.AdaptiveAvgPool2d((2, 2)),
        )
        self.proj = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 2 * 2, output_dim),
            nn.GELU(),
            nn.LayerNorm(output_dim),
        )

    def forward(self, image_tensor: torch.Tensor):
        # image_tensor: [B, 3, H, W]
        gray = image_tensor.mean(dim=1, keepdim=True)
        fft = torch.fft.fft2(gray)
        magnitude = torch.log1p(torch.abs(fft))
        magnitude = torch.fft.fftshift(magnitude, dim=(-2, -1))
        magnitude = (magnitude - magnitude.mean(dim=(-2, -1), keepdim=True)) / (
            magnitude.std(dim=(-2, -1), keepdim=True) + 1e-6
        )
        features = self.encoder(magnitude)
        return self.proj(features)


class HybridImageClassifier(nn.Module):
    def __init__(
        self,
        forensic_dim: int = 17,
        backbone_name: str = 'tf_efficientnet_b4_ns',
        hidden_dim: int = 768,
        freq_dim: int = 256,
        use_freq_branch: bool = True,
    ):
        super().__init__()
        self.backbone = timm.create_model(
            backbone_name,
            pretrained=True,
            num_classes=0,
            global_pool='avg',
        )
        self.backbone_dim = self.backbone.num_features
        self.use_freq_branch = use_freq_branch
        self.freq_dim = freq_dim if use_freq_branch else 0
        self.freq_branch = FrequencyBranch(output_dim=freq_dim) if use_freq_branch else None

        fusion_dim = self.backbone_dim + forensic_dim + self.freq_dim
        self.fusion = nn.Sequential(
            nn.Linear(fusion_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, image_tensor: torch.Tensor, forensic_vector: torch.Tensor):
        image_features = self.backbone(image_tensor)
        parts = [image_features, forensic_vector]
        if self.use_freq_branch:
            freq_features = self.freq_branch(image_tensor)
            parts.append(freq_features)
        fused = torch.cat(parts, dim=1)
        return torch.sigmoid(self.fusion(fused))

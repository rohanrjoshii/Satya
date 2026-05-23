import os
import argparse
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
from utils.reality_checker import RealityChecker
from models.hybrid_image_model import HybridImageClassifier
from training.data_augmentation import get_train_transform, get_eval_transform

FEATURE_DIMENSION = 17

class HybridImageDataset(Dataset):
    def __init__(self, root_dir: str, reality_checker: RealityChecker, transform=None, cache_forensics: bool = True):
        self.root_dir = root_dir
        self.transform = transform
        self.reality_checker = reality_checker
        self.image_folder = datasets.ImageFolder(root_dir)
        self.cache_forensics = cache_forensics
        self._feature_cache = {}

    def __len__(self):
        return len(self.image_folder)

    def __getitem__(self, idx):
        path, label = self.image_folder.samples[idx]
        image = Image.open(path).convert('RGB')
        image_tensor = self.transform(image) if self.transform else transforms.ToTensor()(image)

        if self.cache_forensics and path in self._feature_cache:
            forensic_vector = self._feature_cache[path]
        else:
            payload = self.reality_checker.get_forensic_feature_vector(path)
            if payload is None:
                raise RuntimeError(f"Cannot extract forensic features from {path}")
            forensic_vector = payload['vector']
            if self.cache_forensics:
                self._feature_cache[path] = forensic_vector

        return image_tensor, torch.from_numpy(forensic_vector), torch.tensor(label, dtype=torch.float32)


def create_dataloader(data_dir: str, reality_checker: RealityChecker, batch_size: int, num_workers: int, shuffle: bool = True):
    transform = get_train_transform() if shuffle else get_eval_transform()
    dataset = HybridImageDataset(data_dir, reality_checker, transform=transform)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, pin_memory=True)


def train_epoch(model, data_loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, forensic_vectors, labels in data_loader:
        images = images.to(device)
        forensic_vectors = forensic_vectors.to(device)
        labels = labels.to(device).unsqueeze(1)

        optimizer.zero_grad()
        outputs = model(images, forensic_vectors)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        preds = (outputs >= 0.5).float()
        correct += (preds == labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


def validate_epoch(model, data_loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, forensic_vectors, labels in data_loader:
            images = images.to(device)
            forensic_vectors = forensic_vectors.to(device)
            labels = labels.to(device).unsqueeze(1)
            outputs = model(images, forensic_vectors)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            preds = (outputs >= 0.5).float()
            correct += (preds == labels).sum().item()
            total += images.size(0)

    return total_loss / total, correct / total


def export_onnx(model, output_path: str, image_size=(384, 384), device='cpu'):
    model.eval()
    dummy_image = torch.randn(1, 3, image_size[0], image_size[1], device=device)
    dummy_forensics = torch.randn(1, FEATURE_DIMENSION, device=device)
    torch.onnx.export(
        model,
        (dummy_image, dummy_forensics),
        output_path,
        input_names=['image', 'forensic_features'],
        output_names=['score'],
        dynamic_axes={
            'image': {0: 'batch_size'},
            'forensic_features': {0: 'batch_size'},
            'score': {0: 'batch_size'},
        },
        opset_version=17,
    )
    print(f"Exported ONNX model to {output_path}")


def train_image_model():
    parser = argparse.ArgumentParser(description='Train the VerifAI hybrid image detector')
    parser.add_argument('--train-dir', type=str, default='data/train', help='Training data directory')
    parser.add_argument('--val-dir', type=str, default='data/val', help='Validation data directory')
    parser.add_argument('--epochs', type=int, default=12, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size')
    parser.add_argument('--lr', type=float, default=3e-4, help='Learning rate')
    parser.add_argument('--backbone', type=str, default='tf_efficientnet_b4_ns', help='timm backbone name')
    parser.add_argument('--hidden-dim', type=int, default=768, help='Fusion hidden dimension')
    parser.add_argument('--output', type=str, default='backend/models/hybrid_image_detector.pth', help='Checkpoint path')
    parser.add_argument('--onnx-output', type=str, default='backend/models/hybrid_image_detector.onnx', help='ONNX export path')
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu', help='Compute device')
    parser.add_argument('--num-workers', type=int, default=4, help='Data loader workers')
    args = parser.parse_args()

    print('Starting VerifAI hybrid training pipeline...')
    reality_checker = RealityChecker(device='cpu')
    train_loader = create_dataloader(args.train_dir, reality_checker, args.batch_size, args.num_workers, shuffle=True)
    val_loader = create_dataloader(args.val_dir, reality_checker, args.batch_size, args.num_workers, shuffle=False)

    model = HybridImageClassifier(
        forensic_dim=FEATURE_DIMENSION,
        backbone_name=args.backbone,
        hidden_dim=args.hidden_dim,
        use_freq_branch=True,
    )
    model.to(args.device)

    criterion = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, args.epochs))

    best_val_acc = 0.0
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, args.device)
        val_loss, val_acc = validate_epoch(model, val_loader, criterion, args.device)
        scheduler.step()

        print(
            f"Epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} train_acc={train_acc:.4f}"
            f" | val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint = {
                'state_dict': model.state_dict(),
                'config': {
                    'backbone': args.backbone,
                    'hidden_dim': args.hidden_dim,
                    'forensic_dim': FEATURE_DIMENSION,
                }
            }
            torch.save(checkpoint, args.output)
            print(f"Saved checkpoint to {args.output}")

    print(f"Training complete. Best validation accuracy: {best_val_acc:.4f}")
    export_onnx(model, args.onnx_output, device=args.device)


if __name__ == '__main__':
    train_image_model()

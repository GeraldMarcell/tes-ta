"""Shared, offline-only utilities for the exploratory FoodBD pilot."""
from __future__ import annotations

import ast
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import Dataset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/FoodBD"
OUT = ROOT / "outputs/foodbd_pilot"
MANIFESTS = OUT / "manifests"
CHECKPOINTS = OUT / "checkpoints"
METRICS = OUT / "metrics"
PREDICTIONS = OUT / "predictions"
VISUALIZATIONS = OUT / "visualizations"
REPORTS = ROOT / "reports/foodbd_pilot"
SEED = 42
IMAGE_SIZE = 224
SEGMENT_SIZE = 160
NORMAL_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
NORMAL_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def classes() -> list[str]:
    text = (DATA / "data.yaml").read_text(encoding="utf-8")
    return ast.literal_eval(next(line[7:].strip() for line in text.splitlines() if line.startswith("names: ")))


CLASSES = classes()


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def ensure_dirs() -> None:
    for path in (MANIFESTS, CHECKPOINTS, METRICS, PREDICTIONS, VISUALIZATIONS, REPORTS):
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def image_tensor(path: Path, size: int = IMAGE_SIZE) -> torch.Tensor:
    with Image.open(path) as im:
        im = im.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
        arr = np.asarray(im, dtype=np.float32) / 255.0
    arr = (arr - NORMAL_MEAN) / NORMAL_STD
    return torch.from_numpy(arr.transpose(2, 0, 1).copy())


def rasterize_binary(label_path: Path, size: int = SEGMENT_SIZE) -> torch.Tensor:
    """Rasterize every polygon as food=1; overlaps and duplicate lines are idempotent."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    for line in label_path.read_text(encoding="utf-8-sig").splitlines():
        tokens = line.split()
        if not tokens:
            continue
        vals = [float(x) for x in tokens[1:]]
        pts = [(max(0, min(size - 1, round(vals[i] * (size - 1)))),
                max(0, min(size - 1, round(vals[i + 1] * (size - 1)))))
               for i in range(0, len(vals), 2)]
        if len(pts) >= 3:
            draw.polygon(pts, fill=1)
    return torch.from_numpy((np.asarray(mask, dtype=np.uint8) > 0).astype(np.float32)).unsqueeze(0)


class FoodBDSet(Dataset):
    def __init__(self, rows: list[dict[str, str]], task: str, size: int = IMAGE_SIZE):
        self.rows, self.task, self.size = rows, task, size

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        image = image_tensor(DATA / row["image_relpath"], self.size)
        if self.task == "recognition":
            target = torch.zeros(len(CLASSES), dtype=torch.float32)
            for class_id in row["class_ids"].split(";"):
                if class_id:
                    target[int(class_id)] = 1.0
            return image, target
        if self.task == "segmentation":
            mask = rasterize_binary(DATA / row["label_relpath"], self.size)
            return image, mask
        if self.task == "nutrition":
            target = torch.tensor([float(row[k]) for k in ("CHO", "Protein", "Fat")], dtype=torch.float32)
            return image, target
        raise ValueError(self.task)


def make_effnet(num_outputs: int, pretrained: bool = False) -> nn.Module:
    from torchvision.models import efficientnet_b0
    model = efficientnet_b0(weights=None)
    if pretrained:
        path = Path(torch.hub.get_dir()) / "checkpoints" / "efficientnet_b0_rwightman-7f5810bc.pth"
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Local EfficientNet-B0 ImageNet checkpoint missing: {path}")
        model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True), strict=True)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_outputs)
    return model


class ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.layers(x)


class UNet(nn.Module):
    def __init__(self, base: int = 16):
        super().__init__()
        self.enc1 = ConvBlock(3, base)
        self.enc2 = ConvBlock(base, base * 2)
        self.enc3 = ConvBlock(base * 2, base * 4)
        self.enc4 = ConvBlock(base * 4, base * 8)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = ConvBlock(base * 8, base * 16)
        self.up4 = nn.ConvTranspose2d(base * 16, base * 8, 2, stride=2)
        self.dec4 = ConvBlock(base * 16, base * 8)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.dec3 = ConvBlock(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = ConvBlock(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = ConvBlock(base * 2, base)
        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        b = self.bottleneck(self.pool(e4))
        d4 = self.dec4(torch.cat((self.up4(b), e4), 1))
        d3 = self.dec3(torch.cat((self.up3(d4), e3), 1))
        d2 = self.dec2(torch.cat((self.up2(d3), e2), 1))
        d1 = self.dec1(torch.cat((self.up1(d2), e1), 1))
        return self.out(d1)


def dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    prob = torch.sigmoid(logits).flatten(1)
    target = target.flatten(1)
    return 1.0 - ((2 * (prob * target).sum(1) + eps) / (prob.sum(1) + target.sum(1) + eps)).mean()


def device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def list_files() -> list[Path]:
    return [p for split in ("train", "valid", "test") for p in sorted((DATA / split / "images").glob("*.jpg"))]

"""Prepare a group-aware ECUSTFD crop split; train MobileNetV2 only with --train."""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DATA = Path(__import__("os").environ.get("ECUSTFD_ROOT", PROJECT / "data/raw/ECUSTFD"))
SPLIT_FILE = PROJECT / "data/splits/recognition_train_val.csv"
SEED = 42
VAL_FRACTION = 0.2
CLASSES = (
    "apple", "banana", "bread", "bun", "doughnut", "egg",
    "fired_dough_twist", "grape", "lemon", "litchi", "mango",
    "mooncake", "orange", "peach", "pear", "plum", "qiwi", "sachima", "tomato",
)
GROUP_RE = re.compile(r"^(.+?\d+)[ST]\(\d+\)$", re.IGNORECASE)


def object_group(image_id: str) -> str:
    match = GROUP_RE.fullmatch(image_id)
    if not match:
        raise ValueError(f"Cannot derive provisional object group from image ID: {image_id}")
    return match.group(1).lower()


def create_manifest() -> list[dict[str, str]]:
    images = {p.stem.lower(): p for p in (DATA / "JPEGImages").iterdir() if p.is_file()}
    official_ids = [s.strip() for s in (DATA / "ImageSets/Main/trainval.txt").read_text().splitlines() if s.strip()]
    samples: list[dict[str, str]] = []
    group_classes: dict[str, set[str]] = defaultdict(set)
    for image_id in official_ids:
        image = images.get(image_id.lower())
        xml_path = DATA / "Annotations" / f"{image_id}.xml"
        if image is None or not xml_path.is_file():
            raise FileNotFoundError(f"Missing image/XML for official trainval ID {image_id}")
        group = object_group(image_id)
        root = ET.parse(xml_path).getroot()
        for obj_index, obj in enumerate(root.findall("object")):
            label = (obj.findtext("name") or "").strip().lower()
            if label == "coin":
                continue
            if label not in CLASSES:
                raise ValueError(f"Unexpected food class {label!r} in {xml_path.name}")
            box = obj.find("bndbox")
            if box is None or any(box.findtext(k) is None for k in ("xmin", "ymin", "xmax", "ymax")):
                raise ValueError(f"Missing bounding box for {label} in {xml_path.name}")
            coords = [int(box.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax")]
            samples.append({
                "image_id": image.stem,
                "image_path": image.relative_to(DATA).as_posix(),
                "object_index": str(obj_index),
                "label": label,
                "group_id": group,
                "xmin": str(coords[0]), "ymin": str(coords[1]),
                "xmax": str(coords[2]), "ymax": str(coords[3]),
            })
            group_classes[group].add(label)

    # Choose whole groups for validation. Preserve the only group of any class
    # in training, while giving each class with multiple groups validation data.
    groups_by_class: dict[str, set[str]] = defaultdict(set)
    for group, labels in group_classes.items():
        for label in labels:
            groups_by_class[label].add(group)
    targets = {
        label: (min(n - 1, max(1, round(n * VAL_FRACTION))) if n > 1 else 0)
        for label, groups in groups_by_class.items() for n in (len(groups),)
    }
    rng = random.Random(SEED)
    tie_order = list(group_classes)
    rng.shuffle(tie_order)
    rank = {g: i for i, g in enumerate(tie_order)}
    val_counts: Counter[str] = Counter()
    validation_groups: set[str] = set()
    desired_groups = round(len(group_classes) * VAL_FRACTION)
    eligible = {
        group for group, labels in group_classes.items()
        if all(len(groups_by_class[label]) > 1 for label in labels)
    }
    while any(val_counts[label] < targets[label] for label in targets):
        candidates = eligible - validation_groups
        if not candidates:
            break
        scored = []
        for group in candidates:
            score = sum(
                max(0, targets[label] - val_counts[label]) / len(groups_by_class[label])
                for label in group_classes[group]
            )
            scored.append((score, -rank[group], group))
        score, _, chosen = max(scored)
        if score <= 0:
            break
        validation_groups.add(chosen)
        val_counts.update(group_classes[chosen])
    # Keep the split near 80/20 even after class targets have been met.
    desired_groups = max(desired_groups, len(validation_groups))
    candidates = list(eligible - validation_groups)
    rng.shuffle(candidates)
    for group in candidates[:max(0, desired_groups - len(validation_groups))]:
        validation_groups.add(group)

    for row in samples:
        row["split"] = "val" if row["group_id"] in validation_groups else "train"
    SPLIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SPLIT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)
    print(f"Wrote {len(samples)} food-object crops from {len(official_ids)} official trainval images")
    print(f"Groups: {len(validation_groups)} val / {len(group_classes) - len(validation_groups)} train; seed={SEED}")
    counts = Counter((row["split"], row["label"]) for row in samples)
    print("Crop counts by class:", {c: (counts['train', c], counts['val', c]) for c in CLASSES})
    print(f"Manifest: {SPLIT_FILE}")
    return samples


def make_classifier(model_name: str):
    import torch
    from torch import nn
    from torchvision.models import efficientnet_b0, mobilenet_v2, resnet50

    constructors = {
        "mobilenet_v2": mobilenet_v2,
        "efficientnet_b0": efficientnet_b0,
        "resnet50": resnet50,
    }
    weight_files = {
        "mobilenet_v2": "mobilenet_v2-7ebf99e0.pth",
        "efficientnet_b0": "efficientnet_b0_rwightman-7f5810bc.pth",
        "resnet50": "resnet50-0676ba61.pth",
    }
    if model_name not in constructors:
        raise ValueError(f"Unsupported recognition model: {model_name}")
    weight_path = Path(torch.hub.get_dir()) / "checkpoints" / weight_files[model_name]
    if not weight_path.is_file() or weight_path.stat().st_size == 0:
        raise FileNotFoundError(f"Required local ImageNet weights are unavailable: {weight_path}")

    model = constructors[model_name](weights=None)
    state = torch.load(weight_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    # Load the 1,000-class pretrained head first; replace only its final layer.
    if model_name == "mobilenet_v2":
        model.classifier[1] = nn.Linear(model.last_channel, len(CLASSES))
        output_features = model.classifier[1].out_features
    elif model_name == "efficientnet_b0":
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(CLASSES))
        output_features = model.classifier[1].out_features
    else:
        model.fc = nn.Linear(model.fc.in_features, len(CLASSES))
        output_features = model.fc.out_features
    if output_features != len(CLASSES):
        raise RuntimeError(f"{model_name} classifier has {output_features} outputs, expected {len(CLASSES)}")
    return model, weight_path


def train(
    samples: list[dict[str, str]], model_name: str = "mobilenet_v2", *,
    epochs: int = 3, early_stopping_patience: int = 0, run_name: str | None = None,
) -> None:
    try:
        import torch
        from PIL import Image
        from torch import nn
        from torch.utils.data import DataLoader, Dataset
        from torchvision.transforms import Compose, Normalize, Resize, ToTensor
    except ImportError as exc:
        raise SystemExit(f"Training dependencies are unavailable in this environment: {exc}") from exc

    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, weight_path = make_classifier(model_name)
    print(f"Using locally cached ImageNet weights: {weight_path}")

    transform = Compose([Resize((224, 224)), ToTensor(), Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
    class CropDataset(Dataset):
        def __init__(self, split: str):
            self.rows = [r for r in samples if r["split"] == split]
        def __len__(self):
            return len(self.rows)
        def __getitem__(self, i):
            r = self.rows[i]
            with Image.open(DATA / r["image_path"]) as im:
                im = im.convert("RGB")
                xmin, ymin, xmax, ymax = (int(r[k]) for k in ("xmin", "ymin", "xmax", "ymax"))
                # VOC boxes are 1-based inclusive; PIL uses 0-based half-open
                # coordinates. Clamp the converted box to the decoded image.
                left = max(0, min(im.width, xmin - 1))
                top = max(0, min(im.height, ymin - 1))
                right = max(0, min(im.width, xmax))
                bottom = max(0, min(im.height, ymax))
                if right <= left or bottom <= top:
                    raise ValueError(f"Empty clipped bounding box for {r['image_id']} object {r['object_index']}")
                box = (left, top, right, bottom)
                image = transform(im.crop(box))
            return image, CLASSES.index(r["label"])

    train_loader = DataLoader(CropDataset("train"), batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(CropDataset("val"), batch_size=16, shuffle=False, num_workers=0)
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    epoch_metrics = []
    best_accuracy = -1.0
    best_epoch = 0
    best_state = None
    epochs_without_improvement = 0
    started = time.perf_counter()
    for epoch in range(epochs):
        epoch_started = time.perf_counter()
        model.train()
        loss_sum = train_count = 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(images), labels)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(labels)
            train_count += len(labels)
        train_loss = loss_sum / max(train_count, 1)
        model.eval()
        val_loss_sum = correct = total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                logits = model(images)
                val_loss_sum += loss_fn(logits, labels.to(device)).item() * len(labels)
                pred = logits.argmax(1).cpu()
                correct += int((pred == labels).sum())
                total += len(labels)
        val_loss = val_loss_sum / max(total, 1)
        val_accuracy = correct / max(total, 1)
        epoch_seconds = time.perf_counter() - epoch_started
        epoch_metrics.append({
            "epoch": epoch + 1, "train_loss": train_loss,
            "validation_loss": val_loss, "val_accuracy": val_accuracy,
            "epoch_seconds": epoch_seconds,
        })
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_epoch = epoch + 1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
        print(
            f"epoch={epoch + 1} train_loss={train_loss:.4f} "
            f"validation_loss={val_loss:.4f} val_accuracy={val_accuracy:.4f} "
            f"epoch_seconds={epoch_seconds:.2f} samples={total}"
        )
        if early_stopping_patience and epochs_without_improvement >= early_stopping_patience:
            print(f"early_stopping=patience_{early_stopping_patience}_without_accuracy_improvement")
            break

    train_rows = [r for r in samples if r["split"] == "train"]
    val_rows = [r for r in samples if r["split"] == "val"]
    elapsed = time.perf_counter() - started
    config = {
        "model": model_name, "classes": CLASSES, "num_classes": len(CLASSES),
        "seed": SEED, "image_size": 224, "batch_size": 16,
        "epochs": epochs, "completed_epochs": len(epoch_metrics),
        "early_stopping_patience": early_stopping_patience,
        "optimizer": "AdamW", "learning_rate": 1e-3,
        "preprocessing": "RGB crop; VOC 1-based inclusive box clipped and converted to PIL coordinates; resize 224x224; ImageNet mean/std normalization",
        "augmentation": "none",
        "dataset": str(DATA), "split_manifest": str(SPLIT_FILE),
        "train_crops": len(train_rows), "validation_crops": len(val_rows),
        "train_groups": len({r["group_id"] for r in train_rows}),
        "validation_groups": len({r["group_id"] for r in val_rows}),
        "device": str(device), "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "cuda_runtime": torch.version.cuda, "pretrained_weights": str(weight_path),
        "best_epoch": best_epoch, "best_validation_accuracy": best_accuracy,
        "elapsed_seconds": elapsed,
    }
    checkpoint_dir = PROJECT / "outputs/checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    stem = run_name or f"recognition_{model_name}_pilot"
    common = {"config": config, "classes": CLASSES, "seed": SEED, "metrics": epoch_metrics}
    best_path = checkpoint_dir / f"{stem}_best.pt"
    last_path = checkpoint_dir / f"{stem}_last.pt"
    torch.save({**common, "state_dict": best_state, "checkpoint_kind": "best", "epoch": best_epoch}, best_path)
    torch.save({**common, "state_dict": model.state_dict(), "checkpoint_kind": "last", "epoch": len(epoch_metrics)}, last_path)

    metrics_path = PROJECT / "outputs/metrics" / f"{stem}.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps({"config": config, "metrics": epoch_metrics}, indent=2), encoding="utf-8")
    config_path = PROJECT / "outputs/metrics" / f"{stem}_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    report_path = PROJECT / "reports" / f"{stem}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = [
        f"# {model_name} classification experiment",
        "",
        f"- Status: completed {len(epoch_metrics)} of {epochs} maximum epochs; not a final evaluation.",
        f"- Model: {model_name}; ImageNet weights loaded strictly from local cache: `{weight_path}`.",
        f"- Device: {config['device']} ({config['gpu']}); CUDA runtime: {config['cuda_runtime']}.",
        f"- Seed: {SEED}; image size: 224; batch size: 16; optimizer: AdamW (lr=0.001).",
        f"- Data: ECUSTFD food-object crops from official trainval images; group-aware 80/20 split by provisional filename prefix.",
        f"- Split: {len(train_rows)} training crops across {len({r['group_id'] for r in train_rows})} groups; {len(val_rows)} validation crops across {len({r['group_id'] for r in val_rows})} groups.",
        "- The official test split was not used or modified. Grape and lemon have no validation groups in this split.",
        f"- Early stopping patience: {early_stopping_patience} epoch(s) without validation accuracy improvement; stopped after epoch {len(epoch_metrics)}.",
        f"- Best epoch: {best_epoch} (validation accuracy {best_accuracy:.4f}); elapsed training and validation time: {elapsed:.1f} seconds.",
        f"- Best checkpoint: `{best_path}`; final checkpoint: `{last_path}`; metrics: `{metrics_path}`; config: `{config_path}`.",
        "",
        "| Epoch | Training loss | Validation loss | Validation accuracy | Epoch time (s) |",
        "|---:|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {m['epoch']} | {m['train_loss']:.4f} | {m['validation_loss']:.4f} | "
        f"{m['val_accuracy']:.4f} | {m['epoch_seconds']:.2f} |" for m in epoch_metrics
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"best_checkpoint={best_path}")
    print(f"last_checkpoint={last_path}")
    print(f"metrics_config={metrics_path}")
    print(f"config={config_path}")
    print(f"run_report={report_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="run a short three-epoch pilot")
    parser.add_argument("--model", choices=("mobilenet_v2", "efficientnet_b0", "resnet50"), default="mobilenet_v2")
    parser.add_argument("--epochs", type=int, default=3, help="maximum training epochs")
    parser.add_argument("--early-stopping-patience", type=int, default=0,
                        help="stop after this many epochs without validation accuracy improvement; 0 disables")
    parser.add_argument("--run-name", help="artifact filename stem; omit to use the existing pilot names")
    parser.add_argument("--check-models", action="store_true", help="load cached weights and verify 19-class outputs")
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be at least 1")
    if args.early_stopping_patience < 0:
        parser.error("--early-stopping-patience cannot be negative")
    if args.check_models:
        import torch
        for name in ("efficientnet_b0", "resnet50"):
            model, weight_path = make_classifier(name)
            model.eval()
            with torch.inference_mode():
                output = model(torch.zeros(1, 3, 224, 224))
            print(f"{name}: weights={weight_path.name}; output_shape={tuple(output.shape)}")
    elif args.train:
        if not SPLIT_FILE.is_file():
            raise SystemExit("Run without --train first to prepare the group-aware split.")
        with SPLIT_FILE.open(encoding="utf-8", newline="") as f:
            samples = list(csv.DictReader(f))
        train(samples, args.model, epochs=args.epochs,
              early_stopping_patience=args.early_stopping_patience, run_name=args.run_name)
    else:
        create_manifest()


if __name__ == "__main__":
    main()

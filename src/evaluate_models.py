"""Evaluate saved ECUSTFD recognition checkpoints on the fixed validation manifest."""
from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont
from torch.utils.data import DataLoader, Dataset
from torchvision.models import efficientnet_b0, mobilenet_v2, resnet50
from torchvision.transforms import Compose, Normalize, Resize, ToTensor

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data/raw/ECUSTFD"
MANIFEST = PROJECT / "data/splits/recognition_train_val.csv"
OUT = PROJECT / "outputs/evaluation"
REPORT = PROJECT / "reports/recognition_validation_comparison.md"
CHECKPOINTS = {
    "MobileNetV2": ("mobilenet_v2", PROJECT / "outputs/checkpoints/recognition_mobilenet_v2_pilot_best.pt"),
    "EfficientNet-B0": ("efficientnet_b0", PROJECT / "outputs/checkpoints/recognition_efficientnet_b0_pilot_best.pt"),
    "ResNet-50": ("resnet50", PROJECT / "outputs/checkpoints/recognition_resnet50_pilot_best.pt"),
}
TRANSFORM = Compose([
    Resize((224, 224)), ToTensor(),
    Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
])


class ValidationCrops(Dataset):
    def __init__(self, rows: list[dict[str, str]]):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        with Image.open(DATA / r["image_path"]) as im:
            im = im.convert("RGB")
            xmin, ymin, xmax, ymax = (int(r[k]) for k in ("xmin", "ymin", "xmax", "ymax"))
            # Match training: VOC 1-based inclusive to clipped PIL half-open coordinates.
            left = max(0, min(im.width, xmin - 1))
            top = max(0, min(im.height, ymin - 1))
            right = max(0, min(im.width, xmax))
            bottom = max(0, min(im.height, ymax))
            if right <= left or bottom <= top:
                raise ValueError(f"Empty clipped box for {r['image_id']} object {r['object_index']}")
            return TRANSFORM(im.crop((left, top, right, bottom))), r["label"]


def build_model(name: str, nclasses: int):
    from torch import nn
    model = {"mobilenet_v2": mobilenet_v2, "efficientnet_b0": efficientnet_b0,
             "resnet50": resnet50}[name](weights=None)
    if name == "mobilenet_v2":
        model.classifier[1] = nn.Linear(model.last_channel, nclasses)
    elif name == "efficientnet_b0":
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, nclasses)
    else:
        model.fc = nn.Linear(model.fc.in_features, nclasses)
    return model


def score(y_true: list[int], y_pred: list[int], n: int):
    matrix = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
    per_class = []
    supported = []
    for i in range(n):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted = sum(matrix[r][i] for r in range(n))
        # Explicit zero_division=0 where a denominator exists; unsupported class scores are N/A.
        precision = (tp / predicted if predicted else 0.0) if support else None
        recall = tp / support if support else None
        f1 = (2 * precision * recall / (precision + recall) if precision + recall else 0.0) if support else None
        row = {"precision": precision, "recall": recall, "f1-score": f1, "support": support}
        per_class.append(row)
        if support:
            supported.append((row, support))
    total = len(y_true)
    averages = {}
    for metric in ("precision", "recall", "f1-score"):
        averages["macro_" + metric.replace("-score", "")] = sum(r[metric] for r, _ in supported) / len(supported)
        averages["weighted_" + metric.replace("-score", "")] = sum(r[metric] * s for r, s in supported) / total
    return matrix, per_class, {"accuracy": sum(matrix[i][i] for i in range(n)) / total,
                              "samples": total, "macro_class_count": len(supported), **averages}


def save_confusion_png(path: Path, matrix, classes, vmax: int):
    cell, left, top, right, bottom = 27, 180, 50, 20, 135
    width, height = left + cell * len(classes) + right, top + cell * len(classes) + bottom
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    d.text((left, 15), "Confusion matrix (true rows, predicted columns)", fill="black", font=font)
    for i, label in enumerate(classes):
        y = top + i * cell
        d.text((5, y + 8), label[:25], fill="black", font=font)
        for j in range(len(classes)):
            x = left + j * cell
            value = matrix[i][j]
            shade = 255 - int(190 * value / max(vmax, 1))
            d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(shade, shade, 255))
            if value:
                d.text((x + 9, y + 8), str(value), fill="black", font=font)
    d.text((left, top + cell * len(classes) + 12),
           "Predicted class indices: " + ", ".join(f"{i}={c}" for i, c in enumerate(classes)),
           fill="black", font=font)
    im.save(path)


def main():
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        manifest_rows = list(csv.DictReader(f))
    val_rows = [r for r in manifest_rows if r["split"] == "val"]
    if not val_rows:
        raise RuntimeError("Manifest contains no validation samples")
    if any(r["split"] not in ("train", "val") for r in manifest_rows):
        raise RuntimeError("Unexpected split in manifest; refusing evaluation")

    checkpoints = {}
    for display, (name, path) in CHECKPOINTS.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        # weights_only prevents arbitrary pickle object loading.
        ckpt = torch.load(path, map_location="cpu", weights_only=True)
        classes = tuple(ckpt["classes"])
        if len(classes) != 19 or len(set(classes)) != 19:
            raise ValueError(f"{display}: expected 19 unique checkpoint classes, got {classes}")
        if "classes" in checkpoints and classes != checkpoints["classes"]:
            raise ValueError(f"Checkpoint class order mismatch: {display}")
        if any(r["label"] not in classes for r in val_rows):
            raise ValueError(f"Manifest has a label absent from {display} checkpoint classes")
        checkpoints[display] = {"name": name, "path": path, "ckpt": ckpt, "classes": classes}
    classes = checkpoints["MobileNetV2"]["classes"]
    if len(val_rows) != 350:
        print(f"Notice: validation manifest has {len(val_rows)} rows (expected historical count 350)")
    supports = Counter(r["label"] for r in val_rows)
    if sum(supports.values()) != len(val_rows):
        raise RuntimeError("Validation support count mismatch")
    true_labels = [r["label"] for r in val_rows]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    OUT.mkdir(parents=True, exist_ok=True)

    result_by_model = {}
    for display, info in checkpoints.items():
        ckpt = info["ckpt"]
        model = build_model(info["name"], len(classes))
        model.load_state_dict(ckpt["state_dict"], strict=True)
        model.to(device).eval()
        loader = DataLoader(ValidationCrops(val_rows), batch_size=16, shuffle=False, num_workers=0)
        preds = []
        if device.type == "cuda":
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            for images, _labels in loader:
                output = model(images.to(device))
                preds.extend(output.argmax(1).cpu().tolist())
        if device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        if len(preds) != len(val_rows):
            raise RuntimeError(f"{display}: {len(preds)} predictions for {len(val_rows)} rows")
        y_true = [classes.index(label) for label in true_labels]
        matrix, per_class, metrics = score(y_true, preds, len(classes))
        if len(matrix) != 19 or any(len(row) != 19 for row in matrix) or sum(map(sum, matrix)) != len(val_rows):
            raise RuntimeError(f"{display}: confusion matrix validation failed")
        if result_by_model and result_by_model["true_labels"] != true_labels:
            raise RuntimeError("Validation labels differ across models")
        result_by_model["true_labels"] = true_labels
        kind = ckpt.get("checkpoint_kind", "unspecified")
        epoch = ckpt.get("epoch")
        checkpoint_note = f"{kind} checkpoint, epoch {epoch}" if epoch is not None else f"{kind} checkpoint"
        metrics.update({"model": display, "checkpoint": str(info["path"]),
                        "checkpoint_status": checkpoint_note, "device": str(device),
                        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU",
                        "inference_seconds": elapsed,
                        "samples_per_second": len(val_rows) / elapsed if elapsed else None,
                        "zero_division": 0, "unsupported_class_metrics": None})
        result_by_model[display] = {"matrix": matrix, "per_class": per_class, "metrics": metrics}

    vmax = max(max(max(row) for row in result_by_model[m]["matrix"]) for m in CHECKPOINTS)
    for display, info in checkpoints.items():
        slug = info["name"]
        result = result_by_model[display]
        cm_path = OUT / f"{slug}_confusion_matrix.csv"
        with cm_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["true_label\\predicted_label", *classes])
            for label, row in zip(classes, result["matrix"]):
                writer.writerow([label, *row])
        save_confusion_png(OUT / f"{slug}_confusion_matrix.png", result["matrix"], classes, vmax)
        report_path = OUT / f"{slug}_classification_report.csv"
        with report_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["class", "precision", "recall", "f1-score", "support"])
            writer.writeheader()
            for label, row in zip(classes, result["per_class"]):
                writer.writerow({"class": label, **row})
            for avg in ("macro avg", "weighted avg"):
                metric_key = avg.split()[0]
                writer.writerow({"class": avg,
                                 "precision": result["metrics"][metric_key + "_precision"],
                                 "recall": result["metrics"][metric_key + "_recall"],
                                 "f1-score": result["metrics"][metric_key + "_f1"],
                                 "support": len(val_rows)})
        (OUT / f"{slug}_metrics.json").write_text(
            json.dumps({"metrics": result["metrics"], "classes": classes,
                        "support_by_class": {c: supports[c] for c in classes}}, indent=2), encoding="utf-8")

    lines = ["# Recognition validation comparison", "",
             f"Validation-only evaluation of {len(val_rows)} manifest crops; test split was not read. All models used the same ordered rows, 19-class order, RGB VOC-clipped object crops, 224×224 resize, and ImageNet normalization.",
             f"Device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'}). Evaluation used `model.eval()` and `torch.inference_mode()`; timing includes crop loading and preprocessing.",
             "", "| Model/checkpoint | Accuracy | Macro P/R/F1 | Weighted P/R/F1 | N | Inference (s) |",
             "|---|---:|---:|---:|---:|---:|"]
    for display in CHECKPOINTS:
        m = result_by_model[display]["metrics"]
        lines.append(f"| {display} ({m['checkpoint_status']}) | {m['accuracy']:.4f} | {m['macro_precision']:.4f} / {m['macro_recall']:.4f} / {m['macro_f1']:.4f} | {m['weighted_precision']:.4f} / {m['weighted_recall']:.4f} / {m['weighted_f1']:.4f} | {m['samples']} | {m['inference_seconds']:.2f} |")
    lines += ["", "## Validation support by class", "",
              "| Class | Samples |", "|---|---:|"]
    lines.extend(f"| {c} | {supports[c]} |" for c in classes)
    lines += ["", "Grape and lemon have zero validation support. Their per-class precision, recall, and F1 are blank/N/A in CSV because they cannot be evaluated; macro averages include only the 17 supported classes. For supported classes with a zero precision denominator, `zero_division=0` is used. Confusion matrices retain all 19 classes. All three evaluated files are saved best checkpoints, but this three-epoch pilot on a small validation set is not a definitive model ranking.",
              "", "Artifacts: per-model confusion matrix CSV/PNG, classification report CSV, and metrics JSON are in `outputs/evaluation/`.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"device={device}; validation_samples={len(val_rows)}; classes={len(classes)}")
    for display in CHECKPOINTS:
        m = result_by_model[display]["metrics"]
        print(f"{display}: accuracy={m['accuracy']:.4f}; macro_f1={m['macro_f1']:.4f}; weighted_f1={m['weighted_f1']:.4f}; n={m['samples']}; seconds={m['inference_seconds']:.2f}; {m['checkpoint_status']}")
    print(f"report={REPORT}; artifacts={OUT}")


if __name__ == "__main__":
    main()

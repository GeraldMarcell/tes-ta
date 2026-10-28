"""Evaluate the extended-best EfficientNet checkpoint on the fixed validation manifest."""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from evaluate_models import (  # noqa: E402
    DATA, MANIFEST, ValidationCrops, build_model, save_confusion_png, score,
)
from torch.utils.data import DataLoader  # noqa: E402

CHECKPOINT = PROJECT / "outputs/checkpoints/recognition_efficientnet_b0_extended_best.pt"
PILOT_METRICS = PROJECT / "outputs/evaluation/efficientnet_b0_metrics.json"
OUT = PROJECT / "outputs/evaluation/efficientnet_b0_extended_best"


def main() -> None:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    val_rows = [r for r in rows if r["split"] == "val"]
    if len(val_rows) != 350:
        raise RuntimeError(f"Expected 350 validation rows, got {len(val_rows)}")
    if any(r["split"] not in ("train", "val") for r in rows):
        raise RuntimeError("Unexpected manifest split; refusing to evaluate")

    ckpt = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    classes = tuple(ckpt["classes"])
    if ckpt.get("checkpoint_kind") != "best" or ckpt.get("epoch") != 6:
        raise RuntimeError(f"Unexpected checkpoint metadata: kind={ckpt.get('checkpoint_kind')}, epoch={ckpt.get('epoch')}")
    if len(classes) != 19 or len(set(classes)) != 19:
        raise RuntimeError(f"Expected 19 unique classes, got {classes}")
    if any(r["label"] not in classes for r in val_rows):
        raise RuntimeError("Validation manifest includes a label missing from checkpoint class order")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("efficientnet_b0", len(classes))
    model.load_state_dict(ckpt["state_dict"], strict=True)
    model.to(device).eval()
    loader = DataLoader(ValidationCrops(val_rows), batch_size=16, shuffle=False, num_workers=0)
    logits_parts = []
    if device.type == "cuda":
        torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.inference_mode():
        for images, _labels in loader:
            logits_parts.append(model(images.to(device)).cpu())
    if device.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    logits = torch.cat(logits_parts, dim=0)
    if logits.shape != (350, 19):
        raise RuntimeError(f"Unexpected logits shape: {tuple(logits.shape)}")
    probs = logits.softmax(dim=1)
    pred_ids = probs.argmax(dim=1).tolist()
    confidences = probs.max(dim=1).values.tolist()
    true_ids = [classes.index(r["label"]) for r in val_rows]
    predictions = [classes[i] for i in pred_ids]
    matrix, per_class, metrics = score(true_ids, pred_ids, len(classes))
    if len(pred_ids) != 350 or len(matrix) != 19 or any(len(row) != 19 for row in matrix) or sum(map(sum, matrix)) != 350:
        raise RuntimeError("Prediction count or confusion matrix verification failed")

    supports = Counter(r["label"] for r in val_rows)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "confusion_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["true_label\\predicted_label", *classes])
        for label, row in zip(classes, matrix):
            writer.writerow([label, *row])
    save_confusion_png(OUT / "confusion_matrix.png", matrix, classes, max(map(max, matrix)))
    with (OUT / "classification_report.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["class", "precision", "recall", "f1-score", "support"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for label, values in zip(classes, per_class):
            writer.writerow({"class": label, **values})
        for avg in ("macro", "weighted"):
            writer.writerow({"class": f"{avg} avg", "precision": metrics[f"{avg}_precision"],
                             "recall": metrics[f"{avg}_recall"], "f1-score": metrics[f"{avg}_f1"], "support": 350})

    mistakes = []
    for i, (row, pred, confidence) in enumerate(zip(val_rows, predictions, confidences)):
        if pred != row["label"]:
            mistakes.append({
                "validation_index": i,
                "image_id": row["image_id"],
                "object_index": row["object_index"],
                "true_label": row["label"],
                "predicted_label": pred,
                "confidence": confidence,
                "group_id": row["group_id"],
                "image_path": str((DATA / row["image_path"]).resolve()),
            })
    mistake_fields = ["validation_index", "image_id", "object_index", "true_label", "predicted_label", "confidence", "group_id", "image_path"]
    with (OUT / "misclassified_samples.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=mistake_fields)
        writer.writeheader()
        writer.writerows(mistakes)

    tomato_rows = [
        {"image_id": r["image_id"], "object_index": r["object_index"], "true_label": r["label"],
         "predicted_label": predictions[i], "confidence": confidences[i], "group_id": r["group_id"],
         "image_path": str((DATA / r["image_path"]).resolve())}
        for i, r in enumerate(val_rows) if r["image_id"] == "tomato001S(4)"
    ]
    pilot = json.loads(PILOT_METRICS.read_text(encoding="utf-8"))["metrics"]
    metrics.update({
        "model": "EfficientNet-B0", "checkpoint": str(CHECKPOINT), "checkpoint_status": "best checkpoint, epoch 6",
        "checkpoint_kind": ckpt["checkpoint_kind"], "best_epoch": ckpt["epoch"], "classes": list(classes),
        "device": str(device), "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU",
        "inference_seconds": elapsed, "samples_per_second": 350 / elapsed if elapsed else None,
        "zero_division": 0, "unsupported_class_metrics": None, "support_by_class": {c: supports[c] for c in classes},
        "prediction_count": len(pred_ids), "confusion_matrix_shape": [len(matrix), len(matrix[0])],
        "confusion_matrix_sum": sum(map(sum, matrix)), "misclassified_count": len(mistakes),
        "tomato001S(4)_validation_rows": tomato_rows,
        "pilot_best_checkpoint_comparison": {
            "source": str(PILOT_METRICS), "checkpoint_status": pilot.get("checkpoint_status"),
            "accuracy": pilot["accuracy"], "macro_f1": pilot["macro_f1"], "weighted_f1": pilot["weighted_f1"],
            "correct": round(pilot["accuracy"] * pilot["samples"]), "samples": pilot["samples"],
        },
    })
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": metrics, "misclassified_samples": mistakes}, indent=2))


if __name__ == "__main__":
    main()

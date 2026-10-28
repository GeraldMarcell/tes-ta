"""Train short FoodBD recognition, binary segmentation, and nutrition pilots."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from collections import Counter

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from foodbd_pilot_common import (
    CHECKPOINTS, CLASSES, IMAGE_SIZE, MANIFESTS, METRICS, OUT, SEGMENT_SIZE,
    FoodBDSet, UNet, device, dice_loss, ensure_dirs, make_effnet, read_csv,
    save_json, seed_everything,
)


def sync(device_: torch.device) -> None:
    if device_.type == "cuda":
        torch.cuda.synchronize(device_)


def data_loaders(task: str, size: int, batch_size: int):
    manifest = read_csv(MANIFESTS / f"{task}_manifest.csv")
    train_rows = [r for r in manifest if r["split"] == "train"]
    val_rows = [r for r in manifest if r["split"] == "valid"]
    if not train_rows or not val_rows:
        raise RuntimeError(f"{task}: empty train or validation split")
    pin = torch.cuda.is_available()
    train = DataLoader(FoodBDSet(train_rows, task, size), batch_size=batch_size,
                       shuffle=True, num_workers=0, pin_memory=pin)
    valid = DataLoader(FoodBDSet(val_rows, task, size), batch_size=batch_size,
                       shuffle=False, num_workers=0, pin_memory=pin)
    return train_rows, val_rows, train, valid


def run_epoch(model, loader, task, device_, optimizer=None, scaler=None, target_mean=None, target_std=None):
    training = optimizer is not None
    model.train(training)
    loss_total = 0.0
    n = 0
    seg_counts = torch.zeros(4, dtype=torch.float64, device=device_)  # intersection, union, pred+, target+
    rec_logits, rec_targets = [], []
    for images, target in loader:
        images = images.to(device_, non_blocking=True)
        target = target.to(device_, non_blocking=True)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            out = model(images)
            if task == "recognition":
                loss = nn.functional.binary_cross_entropy_with_logits(out, target)
                if not training:
                    rec_logits.append(torch.sigmoid(out).cpu().numpy())
                    rec_targets.append(target.cpu().numpy())
            elif task == "segmentation":
                loss = nn.functional.binary_cross_entropy_with_logits(out, target) + dice_loss(out, target)
                if not training:
                    pred = torch.sigmoid(out) >= 0.5
                    truth = target >= 0.5
                    seg_counts[0] += (pred & truth).sum()
                    seg_counts[1] += (pred | truth).sum()
                    seg_counts[2] += pred.sum()
                    seg_counts[3] += truth.sum()
            else:
                normalized = (target - target_mean) / target_std
                loss = nn.functional.smooth_l1_loss(out, normalized)
            if training:
                loss.backward()
                optimizer.step()
        bs = len(images)
        loss_total += float(loss.detach()) * bs
        n += bs
    result = {"loss": loss_total / max(n, 1), "samples": n}
    if task == "segmentation" and not training:
        inter, union, pred_n, target_n = seg_counts.cpu().tolist()
        result.update({
            "pixel_iou": inter / max(union, 1),
            "pixel_dice": 2 * inter / max(pred_n + target_n, 1),
            "pixel_precision": inter / max(pred_n, 1),
            "pixel_recall": inter / max(target_n, 1),
        })
    if task == "recognition" and not training:
        result["probabilities"] = np.concatenate(rec_logits)
        result["targets"] = np.concatenate(rec_targets)
        result["validation_subset_accuracy_at_0_5"] = float(np.all((result["probabilities"] >= 0.5) == result["targets"], axis=1).mean())
    return result


def thresholds_from_validation(prob: np.ndarray, truth: np.ndarray) -> list[dict]:
    result = []
    grid = [i / 100 for i in range(5, 96, 5)]
    for cid, name in enumerate(CLASSES):
        y = truth[:, cid].astype(bool)
        if not y.any() or y.all():
            result.append({"class_id": cid, "class_name": name, "threshold": 0.5,
                           "status": "fallback_0.5_insufficient_positive_or_negative_validation_support"})
            continue
        best_f1, best_t = -1.0, 0.5
        for t in grid:
            pred = prob[:, cid] >= t
            tp = int((pred & y).sum()); fp = int((pred & ~y).sum()); fn = int((~pred & y).sum())
            f1 = 2 * tp / max(2 * tp + fp + fn, 1)
            if f1 > best_f1 or (f1 == best_f1 and abs(t - 0.5) < abs(best_t - 0.5)):
                best_f1, best_t = f1, t
        result.append({"class_id": cid, "class_name": name, "threshold": best_t,
                       "validation_f1_used_for_threshold": best_f1, "status": "selected_on_validation_only"})
    return result


def train(task: str, epochs: int, patience: int, batch_size: int) -> dict:
    seed_everything()
    dev = device()
    size = SEGMENT_SIZE if task == "segmentation" else IMAGE_SIZE
    train_rows, val_rows, train_loader, val_loader = data_loaders(task, size, batch_size)
    if task == "recognition":
        model = make_effnet(len(CLASSES), pretrained=True)
        criterion_name = "BCEWithLogitsLoss"
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
        target_mean = target_std = None
        optimizer_name, lr = "AdamW", 1e-4
    elif task == "segmentation":
        model = UNet(base=16)
        criterion_name = "BCEWithLogitsLoss + soft Dice loss"
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-4)
        target_mean = target_std = None
        optimizer_name, lr = "AdamW", 5e-4
    else:
        model = make_effnet(3, pretrained=True)
        raw = np.asarray([[float(r[k]) for k in ("CHO", "Protein", "Fat")] for r in train_rows], dtype=np.float32)
        target_mean = torch.tensor(raw.mean(0), dtype=torch.float32, device=dev)
        raw_std = raw.std(0)
        raw_std[raw_std < 1e-8] = 1.0
        target_std = torch.tensor(raw_std, dtype=torch.float32, device=dev)
        criterion_name = "SmoothL1Loss on train-standardized targets"
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
        optimizer_name, lr = "AdamW", 1e-4
    model.to(dev)
    best_loss = float("inf")
    best_epoch = 0
    best_state = None
    no_improve = 0
    epochs_log = []
    started = time.perf_counter()
    for epoch in range(1, epochs + 1):
        sync(dev); t0 = time.perf_counter()
        tr = run_epoch(model, train_loader, task, dev, optimizer, target_mean=target_mean, target_std=target_std)
        va = run_epoch(model, val_loader, task, dev, target_mean=target_mean, target_std=target_std)
        sync(dev); seconds = time.perf_counter() - t0
        item = {"epoch": epoch, "train_loss": tr["loss"], "validation_loss": va["loss"],
                "epoch_seconds": seconds, "train_samples": tr["samples"], "validation_samples": va["samples"]}
        for key in ("pixel_iou", "pixel_dice", "pixel_precision", "pixel_recall", "validation_subset_accuracy_at_0_5"):
            if key in va: item[key] = va[key]
        epochs_log.append(item)
        if va["loss"] < best_loss:
            best_loss, best_epoch = va["loss"], epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
        print(f"{task} epoch={epoch}/{epochs} train_loss={tr['loss']:.5f} val_loss={va['loss']:.5f} seconds={seconds:.1f}", flush=True)
        if task == "segmentation":
            print(f"  val IoU={va['pixel_iou']:.4f} Dice={va['pixel_dice']:.4f} P={va['pixel_precision']:.4f} R={va['pixel_recall']:.4f}", flush=True)
        if no_improve >= patience:
            print(f"{task} early_stop=validation_loss_not_improved_for_{patience}_epochs")
            break
    elapsed = time.perf_counter() - started
    if best_state is None:
        raise RuntimeError(f"{task}: no best checkpoint was produced")
    config = {
        "task": task, "model": "EfficientNet-B0 multi-label" if task == "recognition" else ("U-Net binary segmentation" if task == "segmentation" else "EfficientNet-B0 image-level multi-output regression"),
        "seed": 42, "device": str(dev), "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else "CPU",
        "torch": torch.__version__, "torchvision": __import__("torchvision").__version__, "cuda_runtime": torch.version.cuda,
        "image_size": size, "batch_size": batch_size, "max_epochs": epochs, "completed_epochs": len(epochs_log),
        "early_stopping_patience": patience, "best_epoch": best_epoch, "best_validation_loss": best_loss,
        "selection_metric": "lowest validation loss", "optimizer": optimizer_name, "learning_rate": lr,
        "weight_decay": 1e-4, "loss": criterion_name, "normalization": "ImageNet mean/std",
        "augmentation": "none", "train_samples": len(train_rows), "validation_samples": len(val_rows),
        "train_groups": len({r["group_id"] for r in train_rows}), "validation_groups": len({r["group_id"] for r in val_rows}),
        "training_seconds": elapsed, "test_used_during_training": False,
        "pretrained_weights": str(Path(torch.hub.get_dir()) / "checkpoints/efficientnet_b0_rwightman-7f5810bc.pth") if task != "segmentation" else "not used; U-Net initialized from scratch",
        "nutrition_target_mean_train_only": target_mean.detach().cpu().tolist() if target_mean is not None else None,
        "nutrition_target_std_train_only": target_std.detach().cpu().tolist() if target_std is not None else None,
        "mask_policy": "binary union of all polygons; duplicate and cross-class overlap are idempotent" if task == "segmentation" else None,
    }
    prefix = f"foodbd_{task}"
    ckpt_common = {"config": config, "metrics": epochs_log, "classes": CLASSES, "seed": 42}
    best_extra = {}
    if task == "recognition":
        model.load_state_dict(best_state)
        model.eval()
        val = run_epoch(model, val_loader, task, dev)
        best_extra["thresholds"] = thresholds_from_validation(val["probabilities"], val["targets"])
        config["validation_threshold_grid"] = [i / 100 for i in range(5, 96, 5)]
        config["threshold_policy"] = "per-class F1 maximum on validation; fallback 0.5 if class lacks positive or negative support"
    if task == "nutrition":
        best_extra.update({"target_mean": target_mean.detach().cpu(), "target_std": target_std.detach().cpu(),
                           "target_names": ["CHO", "Protein", "Fat"]})
    torch.save({**ckpt_common, **best_extra, "state_dict": best_state, "checkpoint_kind": "best", "epoch": best_epoch}, CHECKPOINTS / f"{prefix}_best.pt")
    torch.save({**ckpt_common, **best_extra, "state_dict": model.state_dict(), "checkpoint_kind": "last", "epoch": len(epochs_log)}, CHECKPOINTS / f"{prefix}_last.pt")
    save_json(METRICS / f"{prefix}.json", {"config": config, "epochs": epochs_log})
    save_json(METRICS / f"{prefix}_config.json", config)
    return {"task": task, "config": config, "epochs": epochs_log}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=("recognition", "segmentation", "nutrition"))
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()
    ensure_dirs()
    limits = {"recognition": 8, "segmentation": 8, "nutrition": 10}
    epochs = args.epochs or limits[args.task]
    if epochs > limits[args.task] or epochs < 1:
        parser.error(f"{args.task} pilot permits 1..{limits[args.task]} epochs")
    batch = args.batch_size or (16 if args.task != "segmentation" else 12)
    if batch < 1 or args.patience < 1:
        parser.error("batch size and patience must be positive")
    result = train(args.task, epochs, args.patience, batch)
    print(json.dumps({"best_epoch": result["config"]["best_epoch"],
                      "completed_epochs": len(result["epochs"]),
                      "training_seconds": result["config"]["training_seconds"],
                      "best_checkpoint": str(CHECKPOINTS / f"foodbd_{args.task}_best.pt"),
                      "last_checkpoint": str(CHECKPOINTS / f"foodbd_{args.task}_last.pt")}, indent=2))


if __name__ == "__main__":
    main()

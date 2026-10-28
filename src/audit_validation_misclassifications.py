"""Reproduce selected validation errors and export audit CSV/contact sheets."""
from __future__ import annotations

import csv
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont, ImageOps
from torch.utils.data import DataLoader

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data/raw/ECUSTFD"
MANIFEST = PROJECT / "data/splits/recognition_train_val.csv"
EVAL = PROJECT / "outputs/evaluation"
OUT_CSV = EVAL / "recognition_misclassified_samples.csv"
CHECKPOINTS = {
    "MobileNetV2": ("mobilenet_v2", "recognition_mobilenet_v2_pilot_best.pt"),
    "EfficientNet-B0": ("efficientnet_b0", "recognition_efficientnet_b0_pilot_best.pt"),
    "ResNet-50": ("resnet50", "recognition_resnet50_pilot_best.pt"),
}
EFF_FOCUS_CLASSES = {"banana", "bun", "litchi", "tomato"}


def expected_confusion(slug, classes):
    with (EVAL / f"{slug}_confusion_matrix.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if tuple(rows[0][1:]) != tuple(classes):
        raise RuntimeError(f"Saved confusion matrix class order differs for {slug}")
    return [[int(v) for v in row[1:]] for row in rows[1:]]


def inspect_annotation(row, image_size):
    xml_path = DATA / "Annotations" / f"{row['image_id']}.xml"
    root = ET.parse(xml_path).getroot()
    xml_filename = (root.findtext("filename") or "").strip()
    objects = root.findall("object")
    index = int(row["object_index"])
    if index >= len(objects):
        raise ValueError(f"XML object index {index} missing: {xml_path}")
    obj = objects[index]
    xml_label = (obj.findtext("name") or "").strip().lower()
    box = obj.find("bndbox")
    if box is None:
        raise ValueError(f"XML bounding box missing: {xml_path}, object {index}")
    coords = {key: int(box.findtext(key)) for key in ("xmin", "ymin", "xmax", "ymax")}
    if coords != {k: int(row[k]) for k in coords}:
        raise ValueError(f"Manifest/XML bbox mismatch: {xml_path}, object {index}")
    width, height = image_size
    xmin, ymin, xmax, ymax = (coords[k] for k in ("xmin", "ymin", "xmax", "ymax"))
    clipped = (max(0, min(width, xmin - 1)), max(0, min(height, ymin - 1)),
               max(0, min(width, xmax)), max(0, min(height, ymax)))
    valid = clipped[2] > clipped[0] and clipped[3] > clipped[1]
    in_bounds = xmin >= 1 and ymin >= 1 and xmax <= width and ymax <= height and xmax >= xmin and ymax >= ymin
    size_node = root.find("size")
    xml_size_match = bool(size_node is not None and int(size_node.findtext("width")) == width
                          and int(size_node.findtext("height")) == height)
    return {
        "xml_path": str(xml_path.resolve()), "xml_filename": xml_filename,
        "xml_filename_matches_image": xml_filename.lower() == Path(row["image_path"]).name.lower(),
        "xml_object_label": xml_label, "xml_label_matches_manifest": xml_label == row["label"],
        **{f"bbox_{k}": v for k, v in coords.items()},
        "bbox_clipped_left": clipped[0], "bbox_clipped_top": clipped[1],
        "bbox_clipped_right": clipped[2], "bbox_clipped_bottom": clipped[3],
        "bbox_valid_after_clipping": valid, "bbox_inside_image_bounds": in_bounds,
        "bbox_was_clipped": clipped != (xmin - 1, ymin - 1, xmax, ymax),
        "bbox_width_px": clipped[2] - clipped[0], "bbox_height_px": clipped[3] - clipped[1],
        "bbox_area_fraction": ((clipped[2]-clipped[0])*(clipped[3]-clipped[1])/(width*height)) if valid else None,
        "image_width": width, "image_height": height, "xml_size_matches_image": xml_size_match,
    }


def thumb(image, bounds, size, draw_box=False):
    image = image.copy()
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    xoff, yoff = (size[0]-image.width)//2, (size[1]-image.height)//2
    canvas.paste(image, (xoff, yoff))
    if draw_box:
        sx, sy = image.width / bounds[0], image.height / bounds[1]
        l, t, r, b = bounds[2]
        rect = (xoff + int(l*sx), yoff + int(t*sy), xoff + int(r*sx), yoff + int(b*sy))
        ImageDraw.Draw(canvas).rectangle(rect, outline="red", width=2)
    return canvas


def save_contact_sheet(model_name, slug, records):
    tile_w, tile_h, image_w, image_h = 420, 205, 195, 145
    cols = 2
    rows = math.ceil(len(records) / cols)
    sheet = Image.new("RGB", (cols*tile_w, rows*tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, rec in enumerate(records):
        x, y = (i % cols)*tile_w, (i // cols)*tile_h
        title = f"{rec['image_id']}  {rec['true_label']} -> {rec['predicted_label']}  p={rec['predicted_confidence']:.3f}"
        draw.text((x+4, y+3), title[:66], fill="black", font=font)
        draw.text((x+4, y+17), f"object {rec['object_index']} | XML label={rec['xml_object_label']} | box valid={rec['bbox_valid_after_clipping']}", fill="black", font=font)
        with Image.open(rec["image_path_absolute"]) as im:
            im = im.convert("RGB")
            box = (rec["bbox_clipped_left"], rec["bbox_clipped_top"],
                   rec["bbox_clipped_right"], rec["bbox_clipped_bottom"])
            full = thumb(im, (im.width, im.height, box), (image_w, image_h), True)
            crop = im.crop(box)
            crop_thumb = thumb(crop, (crop.width, crop.height, (0, 0, crop.width, crop.height)),
                               (image_w, image_h))
            sheet.paste(full, (x+5, y+35))
            sheet.paste(crop_thumb, (x+image_w+15, y+35))
            ImageDraw.Draw(sheet).text((x+5, y+183), "source + bbox", fill="black", font=font)
            ImageDraw.Draw(sheet).text((x+image_w+15, y+183), "object crop", fill="black", font=font)
    path = EVAL / f"misclassification_contact_sheet_{slug}.png"
    sheet.save(path)
    return path


def main():
    # Reuse the exact crop and transform implementation from the evaluator.
    sys.path.insert(0, str((PROJECT / "src").resolve()))
    import evaluate_models as evaluator

    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == "val"]
    if len(rows) != 350:
        raise RuntimeError(f"Expected same 350 validation rows, got {len(rows)}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    records_by_model = {}
    expected_labels = [r["label"] for r in rows]

    for display, (slug, checkpoint_name) in CHECKPOINTS.items():
        checkpoint_path = PROJECT / "outputs/checkpoints" / checkpoint_name
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if ckpt.get("checkpoint_kind") != "best":
            raise RuntimeError(f"Refusing non-best checkpoint: {checkpoint_path}")
        classes = tuple(ckpt["classes"])
        model = evaluator.build_model(slug, len(classes))
        model.load_state_dict(ckpt["state_dict"], strict=True)
        model.to(device).eval()
        loader = DataLoader(evaluator.ValidationCrops(rows), batch_size=16, shuffle=False, num_workers=0)
        predicted, confidences = [], []
        with torch.inference_mode():
            for images, labels in loader:
                probs = torch.softmax(model(images.to(device)), dim=1)
                conf, idx = probs.max(dim=1)
                predicted.extend(classes[k] for k in idx.cpu().tolist())
                confidences.extend(conf.cpu().tolist())
        if len(predicted) != 350 or expected_labels != [r["label"] for r in rows]:
            raise RuntimeError(f"Prediction/label count mismatch for {display}")
        actual_idx = [classes.index(label) for label in expected_labels]
        predicted_idx = [classes.index(label) for label in predicted]
        reproduced, _, _ = evaluator.score(actual_idx, predicted_idx, len(classes))
        if reproduced != expected_confusion(slug, classes):
            raise RuntimeError(f"Reproduced confusion matrix differs from saved evaluation for {display}")

        chosen = []
        for i, (row, pred, confidence) in enumerate(zip(rows, predicted, confidences)):
            true = row["label"]
            if pred == true:
                continue
            if display == "MobileNetV2":
                focus = true == "pear" and pred == "peach"
            elif display == "EfficientNet-B0":
                focus = (true == "pear" and pred == "bun") or true in EFF_FOCUS_CLASSES or pred in EFF_FOCUS_CLASSES
            else:
                focus = true == "plum" and pred == "apple"
            if not focus:
                continue
            row_copy = dict(row)
            image_path = DATA / row["image_path"]
            try:
                with Image.open(image_path) as im:
                    im.load()
                    size = im.size
            except Exception as exc:
                raise RuntimeError(f"Unreadable validation image {image_path}: {exc}") from exc
            annotation = inspect_annotation(row, size)
            row_copy.update(annotation)
            row_copy.update({
                "model": display, "checkpoint": checkpoint_name, "checkpoint_kind": ckpt["checkpoint_kind"],
                "checkpoint_epoch": ckpt["epoch"], "true_label": true, "predicted_label": pred,
                "predicted_confidence": confidence,
                "image_path_relative": row["image_path"], "image_path_absolute": str(image_path.resolve()),
                "image_readable": True,
            })
            # Focus reason makes false-positive and false-negative coverage explicit.
            reasons = []
            if display == "EfficientNet-B0":
                if true in EFF_FOCUS_CLASSES: reasons.append(f"actual_{true}")
                if pred in EFF_FOCUS_CLASSES: reasons.append(f"predicted_{pred}")
                if true == "pear" and pred == "bun": reasons.append("pear_to_bun_priority")
            else:
                reasons.append(f"priority_{true}_to_{pred}")
            row_copy["audit_focus"] = ";".join(reasons)
            chosen.append(row_copy)
        records_by_model[display] = chosen
        print(f"{display}: checkpoint={checkpoint_name} epoch={ckpt['epoch']} reproduced_confusion=exact selected_errors={len(chosen)}")

    fields = ["model", "checkpoint", "checkpoint_kind", "checkpoint_epoch", "audit_focus",
              "image_id", "object_index", "true_label", "predicted_label", "predicted_confidence",
              "group_id", "image_path_relative", "image_path_absolute", "xml_path", "xml_filename",
              "xml_filename_matches_image", "xml_object_label", "xml_label_matches_manifest",
              "bbox_xmin", "bbox_ymin", "bbox_xmax", "bbox_ymax", "bbox_clipped_left",
              "bbox_clipped_top", "bbox_clipped_right", "bbox_clipped_bottom",
              "bbox_valid_after_clipping", "bbox_inside_image_bounds", "bbox_was_clipped",
              "bbox_width_px", "bbox_height_px", "bbox_area_fraction", "image_width", "image_height",
              "xml_size_matches_image", "image_readable"]
    EVAL.mkdir(parents=True, exist_ok=True)
    all_records = [r for display in CHECKPOINTS for r in records_by_model[display]]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)
    print(f"csv={OUT_CSV} rows={len(all_records)}")
    for display, (slug, _filename) in CHECKPOINTS.items():
        path = save_contact_sheet(display, slug, records_by_model[display])
        print(f"contact_sheet_{slug}={path} samples={len(records_by_model[display])}")


if __name__ == "__main__":
    main()

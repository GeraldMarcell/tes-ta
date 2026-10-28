"""Build immutable-source pilot manifests for FoodBD; no weights or training."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

from foodbd_pilot_common import (
    CLASSES, DATA, MANIFESTS, OUT, PREDICTIONS, REPORTS, SEED,
    VISUALIZATIONS, ensure_dirs, read_csv, save_json, write_csv,
)

COLLIDING_IDS = {"FoodBD-0888", "FoodBD-1103", "FoodBD-1217", "FoodBD-3083"}


def dhash(path: Path) -> int:
    with Image.open(path) as im:
        im = ImageOps.grayscale(im).resize((9, 8), Image.Resampling.LANCZOS)
        px = list(im.getdata())
    value = 0
    for y in range(8):
        for x in range(8):
            value = (value << 1) | (px[y * 9 + x] > px[y * 9 + x + 1])
    return value


def main() -> None:
    ensure_dirs()
    meta_rows = read_csv(DATA.parent.parent / "source_archives/FoodBD_v2/root/FoodBD_Meta_data.csv")
    meta = {(r["types"], r["filename"]): r for r in meta_rows}
    nutrition_rows = read_csv(DATA / "MealNutrition1837_All.csv")
    images: list[dict] = []
    for split in ("train", "valid", "test"):
        for image in sorted((DATA / split / "images").glob("*.jpg")):
            label = DATA / split / "labels" / f"{image.stem}.txt"
            rows = [x for x in label.read_text(encoding="utf-8-sig").splitlines() if x.strip()] if label.is_file() else []
            class_ids = sorted({int(x.split()[0]) for x in rows})
            images.append({
                "image_id": image.stem, "group_id": image.stem, "split": split,
                "image_path": image, "label_path": label,
                "image_relpath": image.relative_to(DATA).as_posix(),
                "label_relpath": label.relative_to(DATA).as_posix() if label.is_file() else "",
                "class_ids": ";".join(map(str, class_ids)),
                "class_names": ";".join(CLASSES[c] for c in class_ids),
                "polygon_count": len(rows),
            })

    # Hash every source image once; an exact cross-split duplicate is excluded.
    exact: dict[str, list[dict]] = defaultdict(list)
    for row in images:
        row["sha256"] = hashlib.sha256(row["image_path"].read_bytes()).hexdigest()
        exact[row["sha256"]].append(row)
    reasons: dict[str, set[str]] = defaultdict(set)
    for group in exact.values():
        if len({r["split"] for r in group}) > 1:
            ids = ",".join(sorted({r["image_id"] for r in group}))
            for r in group:
                reasons[r["image_relpath"]].add(f"exact_image_duplicate_across_splits:{ids}")

    # The known repeated basenames and images absent from the exact (split, filename)
    # source metadata are excluded rather than repaired by approximate name matching.
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in images:
        by_id[row["image_id"]].append(row)
        if row["image_id"] in COLLIDING_IDS:
            reasons[row["image_relpath"]].add("same_image_id_occurs_across_official_splits")
        if not row["label_path"].is_file():
            reasons[row["image_relpath"]].add("paired_label_txt_missing")
        if (row["split"], row["image_path"].name) not in meta:
            reasons[row["image_relpath"]].add("no_exact_split_filename_entry_in_source_metadata")

    # Screen cross-split visual near-duplicates. dHash is only a candidate screen;
    # the pilot conservatively excludes both candidates instead of claiming identity.
    candidate_path = OUT / "visualizations/dhash_cross_split_candidates.csv"
    if candidate_path.is_file():
        pairs = read_csv(candidate_path)
    else:
        dh = {r["image_relpath"]: dhash(r["image_path"]) for r in images}
        pairs = []
        for i, a in enumerate(images):
            for b in images[i + 1:]:
                if a["split"] == b["split"] or a["image_id"] == b["image_id"]:
                    continue
                distance = (dh[a["image_relpath"]] ^ dh[b["image_relpath"]]).bit_count()
                if distance <= 2:
                    pairs.append({
                        "dhash_hamming_64": distance,
                        "image_a": a["image_id"], "split_a": a["split"],
                        "image_b": b["image_id"], "split_b": b["split"],
                        "status": "candidate only; both excluded conservatively; visual identity unproven",
                    })
        write_csv(candidate_path, pairs,
                  ["dhash_hamming_64", "image_a", "split_a", "image_b", "split_b", "status"])
    by_file = {(r["split"], r["image_id"]): r for r in images}
    for pair in pairs:
        a = by_file.get((pair["split_a"], pair["image_a"]))
        b = by_file.get((pair["split_b"], pair["image_b"]))
        if a and b:
            reasons[a["image_relpath"]].add(f"cross_split_dhash_candidate_le_2:{b['image_id']}:{b['split']}:distance={pair['dhash_hamming_64']}")
            reasons[b["image_relpath"]].add(f"cross_split_dhash_candidate_le_2:{a['image_id']}:{a['split']}:distance={pair['dhash_hamming_64']}")
    source_sheet = REPORTS / "visual_audit/dhash_cross_split_candidates.png"
    if source_sheet.is_file():
        shutil.copy2(source_sheet, VISUALIZATIONS / "dhash_cross_split_candidates.png")

    eligible: list[dict] = []
    exclusions: list[dict] = []
    for r in images:
        why = sorted(reasons.get(r["image_relpath"], set()))
        if why:
            for reason in why:
                exclusions.append({"pipeline": "recognition;segmentation;nutrition_if_joined", "sample_id": r["image_id"],
                                   "split": r["split"], "source_path": r["image_relpath"], "reason": reason})
        else:
            eligible.append(r)

    manifests: dict[str, list[dict]] = {"train": [], "valid": [], "test": []}
    for r in eligible:
        manifests[r["split"]].append(r)
    manifest_fields = ["image_id", "group_id", "split", "image_relpath", "label_relpath", "class_ids", "class_names", "polygon_count", "sha256"]
    for filename in ("recognition_manifest.csv", "segmentation_manifest.csv"):
        flat = [{k: r[k] for k in manifest_fields} for s in ("train", "valid", "test") for r in manifests[s]]
        write_csv(MANIFESTS / filename, flat, manifest_fields)

    # Exact basename join only. Ambiguous and missing keys are recorded, never guessed.
    nutrition_by_id: dict[str, list[dict]] = defaultdict(list)
    for r in images:
        nutrition_by_id[r["image_id"] + ".jpg"].append(r)
    nutrition_manifest: list[dict] = []
    for nr in nutrition_rows:
        key = nr.get("FoodImage", "").strip()
        matches = nutrition_by_id.get(key, [])
        if len(matches) != 1:
            exclusions.append({"pipeline": "nutrition", "sample_id": key, "split": "", "source_path": "MealNutrition1837_All.csv",
                               "reason": "no_exact_image_match" if not matches else "ambiguous_basename_matches_multiple_images"})
            continue
        image_row = matches[0]
        if image_row not in eligible:
            why = sorted(reasons.get(image_row["image_relpath"], set()))
            exclusions.append({"pipeline": "nutrition", "sample_id": key, "split": image_row["split"],
                               "source_path": image_row["image_relpath"],
                               "reason": "matched_image_excluded:" + "|".join(why)})
            continue
        nutrition_manifest.append({**{k: image_row[k] for k in manifest_fields},
                                   **{k: nr[k] for k in ("CHO", "Protein", "Fat", "Fiber", "Calorie", "GL")}})
    write_csv(MANIFESTS / "nutrition_manifest.csv", nutrition_manifest,
              manifest_fields + ["CHO", "Protein", "Fat", "Fiber", "Calorie", "GL"])
    write_csv(MANIFESTS / "excluded_samples.csv", exclusions,
              ["pipeline", "sample_id", "split", "source_path", "reason"])

    summary = {
        "seed": 42, "source_split_policy": "official train/valid/test folders retained; no file moved",
        "excluded_group_ids": sorted(COLLIDING_IDS),
        "dhash_screen": {"method": "64-bit horizontal difference hash from grayscale 9x8 thumbnails",
                         "cross_split_threshold_hamming": 2, "candidate_pairs": len(pairs),
                         "action": "exclude both images in every candidate pair; candidate relation not asserted"},
        "exact_duplicate_cross_split_groups": sum(1 for g in exact.values() if len({r['split'] for r in g}) > 1),
        "class_names": CLASSES,
        "pipelines": {},
        "nutrition_join": {"source_rows": len(nutrition_rows), "eligible_one_to_one_rows": len(nutrition_manifest),
                           "label_columns": ["CHO", "Protein", "Fat"], "source_units": "not specified in CSV header"},
        "weight_estimation": {"status": "blocked", "reason": "no verified measured-weight target linked to images"},
    }
    for task, rows in (("recognition", [r for s in manifests.values() for r in s]),
                       ("segmentation", [r for s in manifests.values() for r in s])):
        summary["pipelines"][task] = {}
        for split in ("train", "valid", "test"):
            subset = manifests[split]
            counts = Counter(c for r in subset for c in map(int, r["class_ids"].split(";") if r["class_ids"] else []))
            summary["pipelines"][task][split] = {
                "images": len(subset), "polygon_instances": sum(int(r["polygon_count"]) for r in subset),
                "class_presence": {CLASSES[i]: counts[i] for i in range(len(CLASSES))},
                "groups": len({r["group_id"] for r in subset}),
            }
    summary["pipelines"]["nutrition"] = {
        split: {"images": sum(r["split"] == split for r in nutrition_manifest),
                "groups": len({r["group_id"] for r in nutrition_manifest if r["split"] == split})}
        for split in ("train", "valid", "test")
    }
    summary["exclusions"] = {"rows": len(exclusions), "unique_images": len({r["source_path"] for r in exclusions if r["source_path"].endswith(".jpg")})}
    save_json(MANIFESTS / "split_summary.json", summary)
    print(json.dumps({"eligible_images": {s: len(v) for s, v in manifests.items()},
                      "nutrition": summary["nutrition_join"], "dhash_candidate_pairs": len(pairs),
                      "exclusions": summary["exclusions"], "manifests": str(MANIFESTS)}, indent=2))


if __name__ == "__main__":
    main()

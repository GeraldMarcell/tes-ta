# ECUSTFD local dataset inspection

Inspected `C:\TA\data\raw\ECUSTFD` on 2026-10-23. No dataset, environment, or system settings were changed. No models were trained.

## Files and annotations

- `JPEGImages/`, `Annotations/`, `ImageSets/`, and root-level `density.xls` all exist.
- `JPEGImages/` contains 2,978 images; `Annotations/` contains 2,978 XML files. Every image has an XML with the same basename, and all 2,978 XML `<filename>` values match an image. No unmatched files were found.
- XML uses Pascal VOC style `<object>` and `<bndbox>` fields. All parsed boxes had the four expected coordinates. The XMLs checked include dimensions such as 816×551×3, 816×587×3, and 816×612×3.
- Food labels found in XML (object counts): apple 322, banana 212, bread 66, bun 90, doughnut 210, egg 104, fired_dough_twist 124, grape 58, lemon 185, litchi 78, mango 250, orange 281, qiwi 137, tomato 201, pear 182, mooncake 134, peach 126, plum 176, sachima 150. `coin` also appears as a calibration object (2,976 objects), not a food class.
- Every XML root has `<segmented>0`; parsed XMLs provide bounding boxes, with no mask or polygon elements. These boxes do not support supervised pixel segmentation.

## Splits and object grouping

`ImageSets/Main/` contains `train.txt` (622 image IDs), `val.txt` (623), `trainval.txt` (1,245), and `test.txt` (1,733). All are present. The provided train and validation files share 77 apparent food-object IDs, inferred from filename prefixes such as `apple002`; test shares no such IDs with train, val, or trainval. Because multiple S/T-view images share these prefixes, use the prefix as a group in any new split to reduce portion/view leakage. Treat this grouping as filename-based until confirmed by dataset documentation or metadata.

## Measurement CSV, `density.xls`, and environment

`density_export.csv` was read with `;` as delimiter and `,` as decimal separator. It has 174 rows, 160 unique IDs, 174 unique `(id,type)` pairs, and 19 food types. There are no missing cells, invalid numeric values, nonpositive measurements, or exact duplicate records. The 14 repeated IDs are the `mix001`–`mix014` groups, each with two distinct food types. Weight values range from 26 to 448 g. Volume values range from 30 to 450 under the exported `volume(mm^3)` header; those magnitudes look more like cm³/ml than mm³, so the unit needs confirmation before reporting volume errors with physical units.

Measurement matching used an exact image-stem pattern `<id>S(n)` or `<id>T(n)`, then checked the XML objects for the CSV `type` label. All 174 `(id,type)` records matched at least one image group and a same-class XML food object; no records were unmatched. IDs were not joined by class alone. The 14 mixed IDs correctly match distinct food labels within the same image group. This validates the weight targets for object-level regression; volume values are numerically present and image-matched, but their unit is unverified.

The project venv has none of `torch`, `torchvision`, `pandas`, or `datasets`. No PyTorch wheel appears in the pip cache or project, but an ImageNet MobileNetV2 checkpoint is already cached at `C:\Users\user\.cache\torch\hub\checkpoints\mobilenet_v2-7ebf99e0.pth` (about 14 MB). It cannot be used until PyTorch/torchvision are available. No dependencies were installed.

`density.xls` also exists at the dataset root (46,592 bytes; OLE/legacy XLS format). It remains unread because `xlrd` and local XLS conversion tools are unavailable. The CSV export supplies measurement values, so the XLS is not needed for weight matching; its contents could still resolve the volume-unit ambiguity or other metadata.

## Pipeline readiness

- **Food classification: data preparation supported; training blocked by environment.** `src/recognition.py` creates object crops from XML food boxes, excludes `coin`, and writes `data/splits/recognition_train_val.csv`. The generated split contains 1,292 crops from 1,245 official trainval images; 62 provisional groups are train and 20 are validation (seed 42), with zero group overlap. All 19 classes occur in train, while grape and lemon have no validation samples because their available trainval groups are too few to hold out safely. The official test files were not changed. Its 78 filename groups do not overlap the 82 trainval groups; the grouping remains provisional and filename-based. Training was not run because torch/torchvision are absent.
- **Food segmentation: blocked.** Only bounding boxes are present; XML marks all records `segmented=0` and contains no masks/polygons.
- **Portion estimation: weight target supported; volume target unit needs confirmation.** All CSV weight rows map by ID prefix plus XML food class. Use group-aware splitting; multiple views share the same provisional IDs. Volume values map too, but the `mm^3` header appears inconsistent with values 30–450, so confirm units before interpreting physical volume metrics.
- **Nutrition estimation: not yet verified.** No calories or energy values were observed in the XML fields. The workbook could not be read, so calorie targets and their derivation/mapping remain unknown.

## Next step

Confirm the volume unit (the XLS may clarify it), and make PyTorch/torchvision available in the existing venv before any training. Calorie labels remain absent from the verified CSV and XML, so nutrition estimation needs a validated calorie source and image/object join.

## Files created in this continuation

- `src/recognition.py` — reproducible group-aware split preparation and optional three-epoch MobileNetV2 crop-classification pilot; pretrained weights are loaded only from the local cache and no download is attempted.
- `data/splits/recognition_train_val.csv` — generated train/validation crop manifest; raw data and official split files are unchanged.

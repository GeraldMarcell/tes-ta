# Recognition validation comparison

Validation-only evaluation of 350 manifest crops; test split was not read. All models used the same ordered rows, 19-class order, RGB VOC-clipped object crops, 224×224 resize, and ImageNet normalization.
Device: cuda (NVIDIA GeForce RTX 3060). Evaluation used `model.eval()` and `torch.inference_mode()`; timing includes crop loading and preprocessing.

| Model/checkpoint | Accuracy | Macro P/R/F1 | Weighted P/R/F1 | N | Inference (s) |
|---|---:|---:|---:|---:|---:|
| MobileNetV2 (best checkpoint, epoch 1) | 0.8714 | 0.8740 / 0.8819 / 0.8621 | 0.9075 / 0.8714 / 0.8760 | 350 | 2.50 |
| EfficientNet-B0 (best checkpoint, epoch 1) | 0.9686 | 0.9573 / 0.9659 / 0.9600 | 0.9722 / 0.9686 / 0.9695 | 350 | 2.82 |
| ResNet-50 (best checkpoint, epoch 3) | 0.7029 | 0.7553 / 0.7110 / 0.6869 | 0.8054 / 0.7029 / 0.7064 | 350 | 2.97 |

## Validation support by class

| Class | Samples |
|---|---:|
| apple | 34 |
| banana | 24 |
| bread | 16 |
| bun | 8 |
| doughnut | 6 |
| egg | 18 |
| fired_dough_twist | 20 |
| grape | 0 |
| lemon | 0 |
| litchi | 14 |
| mango | 13 |
| mooncake | 32 |
| orange | 12 |
| peach | 16 |
| pear | 40 |
| plum | 44 |
| qiwi | 9 |
| sachima | 24 |
| tomato | 20 |

Grape and lemon have zero validation support. Their per-class precision, recall, and F1 are blank/N/A in CSV because they cannot be evaluated; macro averages include only the 17 supported classes. For supported classes with a zero precision denominator, `zero_division=0` is used. Confusion matrices retain all 19 classes. All three evaluated files are saved best checkpoints, but this three-epoch pilot on a small validation set is not a definitive model ranking.

Artifacts: per-model confusion matrix CSV/PNG, classification report CSV, and metrics JSON are in `outputs/evaluation/`.

# efficientnet_b0 classification experiment

- Status: completed 11 of 15 maximum epochs; not a final evaluation.
- Model: efficientnet_b0; ImageNet weights loaded strictly from local cache: `C:\Users\user\.cache\torch\hub\checkpoints\efficientnet_b0_rwightman-7f5810bc.pth`.
- Device: cuda (NVIDIA GeForce RTX 3060); CUDA runtime: 12.1.
- Seed: 42; image size: 224; batch size: 16; optimizer: AdamW (lr=0.001).
- Data: ECUSTFD food-object crops from official trainval images; group-aware 80/20 split by provisional filename prefix.
- Split: 942 training crops across 62 groups; 350 validation crops across 20 groups.
- The official test split was not used or modified. Grape and lemon have no validation groups in this split.
- Early stopping patience: 5 epoch(s) without validation accuracy improvement; stopped after epoch 11.
- Best epoch: 6 (validation accuracy 0.9914); elapsed training and validation time: 111.5 seconds.
- Best checkpoint: `C:\TA\outputs\checkpoints\recognition_efficientnet_b0_extended_best.pt`; final checkpoint: `C:\TA\outputs\checkpoints\recognition_efficientnet_b0_extended_last.pt`; metrics: `C:\TA\outputs\metrics\recognition_efficientnet_b0_extended.json`; config: `C:\TA\outputs\metrics\recognition_efficientnet_b0_extended_config.json`.

| Epoch | Training loss | Validation loss | Validation accuracy | Epoch time (s) |
|---:|---:|---:|---:|---:|
| 1 | 0.9440 | 0.1851 | 0.9686 | 10.96 |
| 2 | 0.2469 | 0.2965 | 0.9086 | 9.97 |
| 3 | 0.1420 | 0.3827 | 0.8771 | 9.91 |
| 4 | 0.1766 | 0.3635 | 0.8714 | 10.03 |
| 5 | 0.1004 | 0.3263 | 0.9086 | 10.06 |
| 6 | 0.1296 | 0.0693 | 0.9914 | 10.09 |
| 7 | 0.1026 | 0.1774 | 0.9400 | 10.10 |
| 8 | 0.0444 | 0.2638 | 0.9057 | 10.16 |
| 9 | 0.0692 | 0.2289 | 0.9371 | 10.01 |
| 10 | 0.0821 | 0.2206 | 0.9400 | 10.12 |
| 11 | 0.0576 | 0.2054 | 0.9429 | 10.04 |

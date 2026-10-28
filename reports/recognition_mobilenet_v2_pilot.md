# mobilenet_v2 classification pilot

- Status: completed three-epoch smoke-test pilot; not a final evaluation.
- Model: mobilenet_v2; ImageNet weights loaded strictly from local cache: `C:\Users\user\.cache\torch\hub\checkpoints\mobilenet_v2-7ebf99e0.pth`.
- Device: cuda (NVIDIA GeForce RTX 3060); CUDA runtime: 12.1.
- Seed: 42; image size: 224; batch size: 16; optimizer: AdamW (lr=0.001).
- Data: ECUSTFD food-object crops from official trainval images; group-aware 80/20 split by provisional filename prefix.
- Split: 942 training crops across 62 groups; 350 validation crops across 20 groups.
- The official test split was not used or modified. Grape and lemon have no validation groups in this split.
- Best epoch: 1 (validation accuracy 0.8714); elapsed training and validation time: 26.2 seconds.
- Best checkpoint: `C:\TA\outputs\checkpoints\recognition_mobilenet_v2_pilot_best.pt`; final checkpoint: `C:\TA\outputs\checkpoints\recognition_mobilenet_v2_pilot_last.pt`; metrics/config: `C:\TA\outputs\metrics\recognition_mobilenet_v2_pilot.json`.

| Epoch | Training loss | Validation accuracy |
|---:|---:|---:|
| 1 | 1.0551 | 0.8714 |
| 2 | 0.2424 | 0.8514 |
| 3 | 0.1644 | 0.8086 |

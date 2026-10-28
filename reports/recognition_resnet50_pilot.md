# resnet50 classification pilot

- Status: completed three-epoch smoke-test pilot; not a final evaluation.
- Model: resnet50; ImageNet weights loaded strictly from local cache: `C:\Users\user\.cache\torch\hub\checkpoints\resnet50-0676ba61.pth`.
- Device: cuda (NVIDIA GeForce RTX 3060); CUDA runtime: 12.1.
- Seed: 42; image size: 224; batch size: 16; optimizer: AdamW (lr=0.001).
- Data: ECUSTFD food-object crops from official trainval images; group-aware 80/20 split by provisional filename prefix.
- Split: 942 training crops across 62 groups; 350 validation crops across 20 groups.
- The official test split was not used or modified. Grape and lemon have no validation groups in this split.
- Best epoch: 3 (validation accuracy 0.7029); elapsed training and validation time: 44.2 seconds.
- Best checkpoint: `C:\TA\outputs\checkpoints\recognition_resnet50_pilot_best.pt`; final checkpoint: `C:\TA\outputs\checkpoints\recognition_resnet50_pilot_last.pt`; metrics/config: `C:\TA\outputs\metrics\recognition_resnet50_pilot.json`.

| Epoch | Training loss | Validation accuracy |
|---:|---:|---:|
| 1 | 1.8680 | 0.2429 |
| 2 | 1.1450 | 0.6000 |
| 3 | 0.8148 | 0.7029 |

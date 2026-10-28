# efficientnet_b0 classification pilot

- Status: completed three-epoch smoke-test pilot; not a final evaluation.
- Model: efficientnet_b0; ImageNet weights loaded strictly from local cache: `C:\Users\user\.cache\torch\hub\checkpoints\efficientnet_b0_rwightman-7f5810bc.pth`.
- Device: cuda (NVIDIA GeForce RTX 3060); CUDA runtime: 12.1.
- Seed: 42; image size: 224; batch size: 16; optimizer: AdamW (lr=0.001).
- Data: ECUSTFD food-object crops from official trainval images; group-aware 80/20 split by provisional filename prefix.
- Split: 942 training crops across 62 groups; 350 validation crops across 20 groups.
- The official test split was not used or modified. Grape and lemon have no validation groups in this split.
- Best epoch: 1 (validation accuracy 0.9686); elapsed training and validation time: 35.6 seconds.
- Best checkpoint: `C:\TA\outputs\checkpoints\recognition_efficientnet_b0_pilot_best.pt`; final checkpoint: `C:\TA\outputs\checkpoints\recognition_efficientnet_b0_pilot_last.pt`; metrics/config: `C:\TA\outputs\metrics\recognition_efficientnet_b0_pilot.json`.

| Epoch | Training loss | Validation accuracy |
|---:|---:|---:|
| 1 | 0.9442 | 0.9686 |
| 2 | 0.2462 | 0.9114 |
| 3 | 0.1352 | 0.8857 |

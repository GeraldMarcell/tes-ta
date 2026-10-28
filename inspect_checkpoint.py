
import torch

path = r"C:\TA\outputs\checkpoints\recognition_mobilenet_v2_pilot.pt"

checkpoint = torch.load(
    path,
    map_location="cpu",
    weights_only=True
)

print("=== MODEL CHECKPOINT ===")
print("Classes:", checkpoint["classes"])
print("Seed:", checkpoint["seed"])
print("Image size:", checkpoint["image_size"])
print("Batch size:", checkpoint["batch_size"])
print("Epochs:", checkpoint["epochs"])
print("Split manifest:", checkpoint["split_manifest"])


print("\n=== METRICS ===")
metrics = checkpoint["metrics"]

print("Tipe metrics:", type(metrics).__name__)

if isinstance(metrics, dict):
    for key, value in metrics.items():
        print(f"{key}: {value}")
elif isinstance(metrics, (list, tuple)):
    for i, value in enumerate(metrics):
        print(f"Epoch/item {i + 1}: {value}")
else:
    print(metrics)


print("\n=== STATE DICT ===")
print("Jumlah tensor:", len(checkpoint["state_dict"]))
for name, tensor in list(checkpoint["state_dict"].items())[:5]:
    print(name, tuple(tensor.shape))

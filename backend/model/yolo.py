# models/yolo.py
from ultralytics import YOLO
from pathlib import Path

# Use relative path to make it flexible
MODEL_PATH = Path(__file__).parent / "best.pt"

print(f"[yolo] memuat model dari {MODEL_PATH} ...")
model = YOLO(str(MODEL_PATH))
print("[yolo] model siap.")

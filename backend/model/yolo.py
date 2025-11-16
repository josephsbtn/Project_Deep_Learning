# models/yolo.py
from ultralytics import YOLO

# Ubah PATH sesuai lokasi modelmu
MODEL_PATH = r"D:\PROJECT\Project_Deep_Learning\backend\model\best.pt"

print(f"[yolo] memuat model dari {MODEL_PATH} ...")
model = YOLO(MODEL_PATH)
print("[yolo] model siap.")

import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from pathlib import Path

# --- PENGATURAN FITUR (SAKLAR) ---
# Ubah nilai True/False di sini untuk memilih fitur
ENABLE_ENHANCEMENT = True  # Aktifkan CLAHE?
ENABLE_TRACKING_COUNTING = True # Aktifkan Tracking & Region Counting?
# --------------------------------

# --- 1. Fungsi Enhancement (Tidak berubah, sudah benar) ---
def apply_enhancement(image, enhancement_type='CLAHE'):
    """
    Menerapkan Image Enhancement (CLAHE) pada gambar OpenCV (format BGR).
    """
    if image is None: return None
    if enhancement_type == 'CLAHE':
        try:
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            enhanced_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            return enhanced_image
        except cv2.error as e:
            print(f"Error saat menerapkan CLAHE: {e}. Mengembalikan gambar asli.")
            return image
    return image

# --- 2. Fungsi Utama ---
def main():
    # --- PENGATURAN ---
    MODEL_PATH = r"D:\Project_Deep_Learning\backend\utils\best.pt"
    VIDEO_SOURCE_PATH = r"D:\Project_Deep_Learning\backend\dummyData\WhatsApp Video 2025-11-13 at 22.57.44_d3112d67.mp4"
    VIDEO_OUTPUT_PATH = "hasil_video_modular.mp4"

    # --- PENGATURAN REGION COUNTER (GARIS) ---
    LINE_START = sv.Point(0, 360)
    LINE_END = sv.Point(1280, 360)
    # ----------------------------------------

    # === LANGKAH A: Muat Model ===
    print(f"Memuat model dari {MODEL_PATH}...")
    model = YOLO(MODEL_PATH)
    print("Model berhasil dimuat.")

    # === LANGKAH B: Setup Region Counter (HANYA JIKA DIPERLUKAN) ===
    line_counter = None
    line_annotator = None
    box_annotator = None
    label_annotator = None

    if ENABLE_TRACKING_COUNTING:
        print("Mode Tracking & Counting: AKTIF")
        
        # 1. Buat objek LineZone (area garis)
        line_counter = sv.LineZone(start=LINE_START, end=LINE_END)
        
        # 2. Buat objek LineZoneAnnotator
        line_annotator = sv.LineZoneAnnotator(thickness=2)
        
        # 3. Buat objek BoxAnnotator (untuk bounding box)
        box_annotator = sv.BoxAnnotator(thickness=2)
        
        # 4. Buat objek LabelAnnotator (untuk label/teks)
        label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)
    else:
        print("Mode Tracking & Counting: NONAKTIF")

    if ENABLE_ENHANCEMENT:
        print("Mode Enhancement (CLAHE): AKTIF")
    else:
        print("Mode Enhancement (CLAHE): NONAKTIF")

    # === LANGKAH C: Buka File Video (Input & Output) ===
    cap_in = cv2.VideoCapture(VIDEO_SOURCE_PATH)
    if not cap_in.isOpened():
        print(f"Error: Gagal membuka video input di {VIDEO_SOURCE_PATH}")
        return

    frame_width = int(cap_in.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap_in.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap_in.get(cv2.CAP_PROP_FPS))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    cap_out = cv2.VideoWriter(VIDEO_OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))
    
    print(f"Memulai proses video: {VIDEO_SOURCE_PATH}...")

    # === LANGKAH D: Loop Setiap Frame Video ===
    while cap_in.isOpened():
        ret, frame = cap_in.read()
        if not ret:
            print("Video selesai diproses.")
            break

        # Salin frame asli untuk diproses
        frame_to_process = frame.copy()

        # --- FITUR 1: ENHANCEMENT (MODULAR) ---
        if ENABLE_ENHANCEMENT:
            frame_to_process = apply_enhancement(frame_to_process, 'CLAHE')

        # --- FITUR 2: TRACKING & COUNTING (MODULAR) ---
        if ENABLE_TRACKING_COUNTING:
            # 1. Jalankan TRACKING
            results = model.track(frame_to_process, persist=True, tracker="bytetrack.yaml", verbose=False)
            
            # 2. Konversi hasil ke format Supervision
            detections = sv.Detections.from_ultralytics(results[0])
            
            # 3. Trigger Line Counter
            line_counter.trigger(detections=detections)

            # 4. Siapkan label untuk bounding box
            labels = []
            if detections.tracker_id is not None:
                for i in range(len(detections)):
                    class_id = detections.class_id[i]
                    confidence = detections.confidence[i]
                    track_id = detections.tracker_id[i]
                    label = f"#{track_id} {model.names[class_id]} {confidence:0.2f}"
                    labels.append(label)
            else:
                for i in range(len(detections)):
                    class_id = detections.class_id[i]
                    confidence = detections.confidence[i]
                    label = f"{model.names[class_id]} {confidence:0.2f}"
                    labels.append(label)
            
            # 5. Gambar bounding box
            frame_to_process = box_annotator.annotate(
                scene=frame_to_process, 
                detections=detections
            )
            
            # 6. Gambar label/teks
            frame_to_process = label_annotator.annotate(
                scene=frame_to_process,
                detections=detections,
                labels=labels
            )
            
            # 7. Gambar Garis Counter dan Angkanya
            line_annotator.annotate(
                frame=frame_to_process,
                line_counter=line_counter
            )

        # --- LANGKAH E: Simpan Frame Final ---
        cap_out.write(frame_to_process)

    # === LANGKAH F: Selesai ===
    cap_in.release()
    cap_out.release()
    cv2.destroyAllWindows()
    print(f"Video hasil berhasil disimpan di: {VIDEO_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
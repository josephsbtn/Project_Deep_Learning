import os
import uuid
import base64
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from pathlib import Path
from model.yolo import model
from utils.enhancement import apply_enhancement
from utils.tracking import run_tracking
from utils.region import create_line_zone, create_polygon_zone, box_annotator, label_annotator

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
OUTPUT_DIR = Path("static/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def read_image_from_request(field_name="file"):
    if field_name not in request.files:
        return None, "file not found"
    f = request.files[field_name]
    data = f.read()
    npimg = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if img is None:
        return None, "invalid image format"
    return img, None

def image_to_base64(image):
    """Convert OpenCV image to base64 string"""
    _, buffer = cv2.imencode('.jpg', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"

def video_to_base64(video_path):
    """Convert video file to base64 string"""
    with open(video_path, 'rb') as video_file:
        video_data = video_file.read()
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        return f"data:video/mp4;base64,{video_base64}"

# --- Endpoint Enhancement (multi-kind) ---
@app.route("/enhance-image", methods=["POST"])
def enhance_image():
    img, err = read_image_from_request("file")
    
    if err: 
        return jsonify({"error": err}), 400

    kind = request.form.get("kind", "CLAHE")
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    enhanced = apply_enhancement(img, kind, brightness=brightness, contrast=contrast)

    # Return base64
    return jsonify({
        "image": image_to_base64(enhanced),
        "kind": kind
    })

# --- Endpoint Detect Only ---
@app.route("/detect", methods=["POST"])
def detect_only():
    img, err = read_image_from_request("file")
    if err: 
        return jsonify({"error": err}), 400

    results = model(img)[0]
    annotated = results.plot()
    
    detections_list = []
    if results.boxes is not None and len(results.boxes) > 0:
        for box, cls, conf in zip(results.boxes.xyxy.tolist(), results.boxes.cls.tolist(), results.boxes.conf.tolist()):
            detections_list.append({
                "box": box, 
                "class_id": int(cls), 
                "confidence": float(conf), 
                "label": model.names[int(cls)]
            })
    
    return jsonify({
        "image": image_to_base64(annotated),
        "detections": detections_list
    })

# --- Endpoint Tracking Only ---
@app.route("/track", methods=["POST"])
def track_only():
    img, err = read_image_from_request("file")
    if err: 
        return jsonify({"error": err}), 400

    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    
    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    
    # Fixed: handle case when tracker_id is None
    labels = []
    tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
    for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
        if tid is not None:
            labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
        else:
            labels.append(f"{model.names[cid]} {conf:0.2f}")
    
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

    return jsonify({
        "image": image_to_base64(annotated),
        "num_detections": len(detections)
    })

# --- Endpoint Line Counting ---
@app.route("/count-line", methods=["POST"])
def count_line():
    img, err = read_image_from_request("file")
    if err: 
        return jsonify({"error": err}), 400
    
    # Create fresh line zone per request to avoid persistent counting
    line_zone, line_annotator = create_line_zone()
    
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    line_zone.trigger(detections=detections)

    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    
    labels = []
    tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
    for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
        if tid is not None:
            labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
        else:
            labels.append(f"{model.names[cid]} {conf:0.2f}")
    
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    line_annotator.annotate(frame=annotated, line_counter=line_zone)

    return jsonify({
        "image": image_to_base64(annotated),
        "count_in": int(line_zone.in_count),
        "count_out": int(line_zone.out_count)
    })

# --- Endpoint Polygon Counter ---
POLYGON_ZONES = {}

@app.route("/create-polygon", methods=["POST"])
def create_polygon():
    data = request.get_json(force=True)
    points = data.get("points")
    if not points or not isinstance(points, list):
        return jsonify({"error": "points must be list of [x,y] pairs"}), 400
    
    try:
        # Convert to numpy array format expected by supervision
        points_array = np.array(points, dtype=np.int32)
        poly, annot = create_polygon_zone(points_array)
        pid = uuid.uuid4().hex
        POLYGON_ZONES[pid] = (poly, annot)
        return jsonify({"polygon_id": pid})
    except Exception as e:
        return jsonify({"error": f"Failed to create polygon: {str(e)}"}), 400

@app.route("/count-polygon/<polygon_id>", methods=["POST"])
def count_polygon(polygon_id):
    if polygon_id not in POLYGON_ZONES:
        return jsonify({"error": "polygon_id not found"}), 404
    
    poly, annot = POLYGON_ZONES[polygon_id]
    img, err = read_image_from_request("file")
    if err: 
        return jsonify({"error": err}), 400
    
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    poly.trigger(detections=detections)

    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    
    labels = []
    tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
    for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
        if tid is not None:
            labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
        else:
            labels.append(f"{model.names[cid]} {conf:0.2f}")
    
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    annot.annotate(frame=annotated, zone=poly)

    return jsonify({
        "image": image_to_base64(annotated),
        "count_in": int(poly.current_count)
    })

# --- Endpoint Process Video ---
@app.route("/process-video", methods=["POST"])
def process_video():
    video_file = request.files.get("file")
    if video_file is None:
        return jsonify({"error": "file not provided"}), 400

    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    do_track = request.form.get("track", "false").lower() == "true"
    count_mode = request.form.get("count_mode", "none")
    polygon_id = request.form.get("polygon_id", None)

    tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
    video_file.save(str(tmp_in_path))

    cap = cv2.VideoCapture(str(tmp_in_path))
    if not cap.isOpened():
        return jsonify({"error": "Failed to open video"}), 500

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Try H264 codec first, fallback to mp4v if not available
    out_path = OUTPUT_DIR / f"proc_{uuid.uuid4().hex}.mp4"

    # Try different codecs for browser compatibility
    codecs_to_try = ["avc1", "H264", "X264", "mp4v"]
    writer = None

    for codec in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
            if writer.isOpened():
                print(f"[video] Using codec: {codec}")
                break
        except:
            continue

    if writer is None or not writer.isOpened():
        # Last resort: use default codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
        print(f"[video] Using fallback codec: mp4v")

    line_zone = None
    line_annot = None
    poly_zone = None
    poly_annot = None
    
    if count_mode == "line":
        line_zone, line_annot = create_line_zone()
    elif count_mode == "polygon":
        if not polygon_id or polygon_id not in POLYGON_ZONES:
            cap.release()
            writer.release()
            return jsonify({"error": "polygon_id invalid or not provided"}), 400
        poly_zone, poly_annot = POLYGON_ZONES[polygon_id]

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        proc = frame.copy()
        if enhance:
            proc = apply_enhancement(proc, enhancement_kind)

        if do_track:
            det = run_tracking(model, proc)
            proc = box_annotator.annotate(proc, det)
            
            labels = []
            tracker_ids = det.tracker_id if det.tracker_id is not None else [None] * len(det)
            for cid, conf, tid in zip(det.class_id, det.confidence, tracker_ids):
                if tid is not None:
                    labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
                else:
                    labels.append(f"{model.names[cid]} {conf:0.2f}")
            
            proc = label_annotator.annotate(proc, det, labels)

            if count_mode == "line" and line_zone is not None:
                line_zone.trigger(detections=det)
                line_annot.annotate(frame=proc, line_counter=line_zone)
            elif count_mode == "polygon" and poly_zone is not None:
                poly_zone.trigger(detections=det)
                poly_annot.annotate(frame=proc, zone=poly_zone)

        writer.write(proc)
        frame_idx += 1

    cap.release()
    writer.release()

    # Cleanup temp input file
    try:
        tmp_in_path.unlink()
    except:
        pass

    # Return filename instead of base64 for better performance
    result = {
        "video_url": f"/video/{out_path.name}",
        "frames_processed": frame_idx
    }

    if line_zone:
        result.update({
            "count_in": int(line_zone.in_count),
            "count_out": int(line_zone.out_count)
        })
    if poly_zone:
        result.update({
            "count": int(poly_zone.current_count)
        })

    return jsonify(result)

# --- Optional: Keep these for backward compatibility or file management ---
@app.route("/outputs", methods=["GET"])
def list_outputs():
    files = [str(p.name) for p in OUTPUT_DIR.glob("*") if p.is_file()]
    return jsonify({"files": files})

@app.route("/download", methods=["GET"])
def download_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "filename param required"}), 400

    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "file not found"}), 404

    return send_file(str(file_path), as_attachment=True)

@app.route("/video/<filename>", methods=["GET"])
def serve_video(filename):
    """Serve video files with proper headers for browser playback"""
    file_path = OUTPUT_DIR / filename
    print(f"[video] Request for: {filename}")
    print(f"[video] File path: {file_path}")
    print(f"[video] File exists: {file_path.exists()}")

    if not file_path.exists() or not file_path.is_file():
        print(f"[video] ERROR: File not found!")
        return jsonify({"error": "file not found"}), 404

    print(f"[video] Serving video file")
    return send_file(
        str(file_path),
        mimetype='video/mp4',
        as_attachment=False,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
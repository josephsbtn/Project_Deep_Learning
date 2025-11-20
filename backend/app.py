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
CORS(app)
OUTPUT_DIR = Path("static/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Store polygon zones
POLYGON_ZONES = {}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def read_image_from_request(field_name="file"):
    """Read image from request"""
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

def is_video_file(file):
    """Check if uploaded file is a video"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    filename = file.filename.lower()
    return any(filename.endswith(ext) for ext in video_extensions)

def process_frame_detect(frame, enhance=False, enhancement_kind="CLAHE", brightness=0, contrast=0):
    """Process single frame with detection only"""
    proc = frame.copy()
    
    # Apply enhancement if requested
    if enhance:
        proc = apply_enhancement(proc, enhancement_kind, brightness=brightness, contrast=contrast)
    
    # Run detection
    results = model(proc)[0]
    annotated = results.plot()
    
    # Extract detections
    detections_list = []
    if results.boxes is not None and len(results.boxes) > 0:
        for box, cls, conf in zip(results.boxes.xyxy.tolist(), 
                                   results.boxes.cls.tolist(), 
                                   results.boxes.conf.tolist()):
            detections_list.append({
                "box": box,
                "class_id": int(cls),
                "confidence": float(conf),
                "label": model.names[int(cls)]
            })
    
    return annotated, detections_list

def process_frame_track(frame, enhance=False, enhancement_kind="CLAHE", 
                       brightness=0, contrast=0, tracker_cfg="bytetrack.yaml"):
    """Process single frame with tracking"""
    proc = frame.copy()
    
    # Apply enhancement if requested
    if enhance:
        proc = apply_enhancement(proc, enhancement_kind, brightness=brightness, contrast=contrast)
    
    # Run tracking
    detections = run_tracking(model, proc, tracker_cfg=tracker_cfg)
    
    # Annotate with boxes
    annotated = box_annotator.annotate(scene=proc.copy(), detections=detections)
    
    # Create labels with tracker IDs
    labels = []
    tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
    for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
        if tid is not None:
            labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
        else:
            labels.append(f"{model.names[cid]} {conf:0.2f}")
    
    # Annotate with labels
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    
    return annotated, detections, labels

def process_video(input_path, output_path, process_func):
    """Generic video processing function"""
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        return None, "Failed to open video"
    
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    
    # Try different codecs for compatibility
    codecs_to_try = ["avc1", "H264", "X264", "mp4v"]
    writer = None
    
    for codec in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
            if writer.isOpened():
                break
        except:
            continue
    
    if writer is None or not writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    
    frame_count = 0
    results = {}
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame using provided function
        processed_frame, frame_results = process_func(frame, frame_count)
        writer.write(processed_frame)
        
        # Update results
        if frame_results:
            for key, value in frame_results.items():
                results[key] = value
        
        frame_count += 1
    
    cap.release()
    writer.release()
    
    results["frames_processed"] = frame_count
    return results, None

# ============================================================================
# ENDPOINT 1: DETECT
# Supports: Photo & Video
# Features: Detection only + Enhancement
# ============================================================================

@app.route("/detect", methods=["POST"])
def detect():
    """
    Detect objects in image or video
    Form params:
    - file: image or video file
    - enhance: true/false (optional, default: false)
    - enhancement_kind: CLAHE/histogram/gamma (optional, default: CLAHE)
    - brightness: int (optional, default: 0)
    - contrast: int (optional, default: 0)
    """
    if "file" not in request.files:
        return jsonify({"error": "file not found"}), 400
    
    file = request.files["file"]
    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    
    # Check if video or image
    if is_video_file(file):
        # Process video
        tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
        file.save(str(tmp_in_path))
        
        out_path = OUTPUT_DIR / f"detect_{uuid.uuid4().hex}.mp4"
        
        def process_func(frame, frame_idx):
            annotated, detections = process_frame_detect(
                frame, enhance, enhancement_kind, brightness, contrast
            )
            return annotated, {"detections_last_frame": len(detections)}
        
        results, err = process_video(tmp_in_path, out_path, process_func)
        
        # Cleanup
        try:
            tmp_in_path.unlink()
        except:
            pass
        
        if err:
            return jsonify({"error": err}), 500
        
        return jsonify({
            "type": "video",
            "video_url": f"/video/{out_path.name}",
            "frames_processed": results.get("frames_processed", 0),
            "enhancement_applied": enhance
        })
    
    else:
        # Process image
        img, err = read_image_from_request("file")
        if err:
            return jsonify({"error": err}), 400
        
        annotated, detections = process_frame_detect(
            img, enhance, enhancement_kind, brightness, contrast
        )
        
        return jsonify({
            "type": "image",
            "image": image_to_base64(annotated),
            "detections": detections,
            "total_detections": len(detections),
            "enhancement_applied": enhance
        })

# ============================================================================
# ENDPOINT 2: TRACK
# Supports: Photo & Video
# Features: Detection + Tracking + Enhancement
# ============================================================================

@app.route("/track", methods=["POST"])
def track():
    """
    Track objects in image or video
    Form params:
    - file: image or video file
    - enhance: true/false (optional, default: false)
    - enhancement_kind: CLAHE/histogram/gamma (optional, default: CLAHE)
    - brightness: int (optional, default: 0)
    - contrast: int (optional, default: 0)
    - tracker: bytetrack.yaml/botsort.yaml (optional, default: bytetrack.yaml)
    """
    if "file" not in request.files:
        return jsonify({"error": "file not found"}), 400
    
    file = request.files["file"]
    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    
    # Check if video or image
    if is_video_file(file):
        # Process video
        tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
        file.save(str(tmp_in_path))
        
        out_path = OUTPUT_DIR / f"track_{uuid.uuid4().hex}.mp4"
        
        def process_func(frame, frame_idx):
            annotated, detections, labels = process_frame_track(
                frame, enhance, enhancement_kind, brightness, contrast, tracker_cfg
            )
            return annotated, {"detections_last_frame": len(detections)}
        
        results, err = process_video(tmp_in_path, out_path, process_func)
        
        # Cleanup
        try:
            tmp_in_path.unlink()
        except:
            pass
        
        if err:
            return jsonify({"error": err}), 500
        
        return jsonify({
            "type": "video",
            "video_url": f"/video/{out_path.name}",
            "frames_processed": results.get("frames_processed", 0),
            "enhancement_applied": enhance,
            "tracker": tracker_cfg
        })
    
    else:
        # Process image
        img, err = read_image_from_request("file")
        if err:
            return jsonify({"error": err}), 400
        
        annotated, detections, labels = process_frame_track(
            img, enhance, enhancement_kind, brightness, contrast, tracker_cfg
        )
        
        return jsonify({
            "type": "image",
            "image": image_to_base64(annotated),
            "num_detections": len(detections),
            "enhancement_applied": enhance,
            "tracker": tracker_cfg
        })

# ============================================================================
# ENDPOINT 3: COUNT with REGION
# Supports: Photo & Video
# Features: Detection + Tracking + Counting + Enhancement
# ============================================================================

@app.route("/count", methods=["POST"])
def count():
    """
    Count objects crossing a line or inside polygon
    Form params:
    - file: image or video file
    - region_type: line/polygon (required)
    - polygon_id: required if region_type=polygon
    - enhance: true/false (optional, default: false)
    - enhancement_kind: CLAHE/histogram/gamma (optional, default: CLAHE)
    - brightness: int (optional, default: 0)
    - contrast: int (optional, default: 0)
    - tracker: bytetrack.yaml/botsort.yaml (optional, default: bytetrack.yaml)
    """
    if "file" not in request.files:
        return jsonify({"error": "file not found"}), 400
    
    file = request.files["file"]
    region_type = request.form.get("region_type", "line")
    polygon_id = request.form.get("polygon_id", None)
    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    
    # Validate region type
    if region_type not in ["line", "polygon"]:
        return jsonify({"error": "region_type must be 'line' or 'polygon'"}), 400
    
    # Setup counting zone
    if region_type == "line":
        counter_zone, zone_annotator = create_line_zone()
    else:  # polygon
        if not polygon_id or polygon_id not in POLYGON_ZONES:
            return jsonify({"error": "polygon_id invalid or not provided"}), 400
        counter_zone, zone_annotator = POLYGON_ZONES[polygon_id]
    
    # Check if video or image
    if is_video_file(file):
        # Process video
        tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
        file.save(str(tmp_in_path))
        
        out_path = OUTPUT_DIR / f"count_{uuid.uuid4().hex}.mp4"
        
        def process_func(frame, frame_idx):
            # Apply enhancement
            proc = frame.copy()
            if enhance:
                proc = apply_enhancement(proc, enhancement_kind, brightness, contrast)
            
            # Track objects
            detections = run_tracking(model, proc, tracker_cfg=tracker_cfg)
            
            # Trigger counting
            counter_zone.trigger(detections=detections)
            
            # Annotate
            annotated = box_annotator.annotate(scene=proc, detections=detections)
            
            # Labels
            labels = []
            tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
            for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
                if tid is not None:
                    labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
                else:
                    labels.append(f"{model.names[cid]} {conf:0.2f}")
            
            annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
            
            # Annotate counting zone
            if region_type == "line":
                zone_annotator.annotate(frame=annotated, line_counter=counter_zone)
            else:
                zone_annotator.annotate(frame=annotated, zone=counter_zone)
            
            # Return results
            if region_type == "line":
                return annotated, {
                    "count_in": int(counter_zone.in_count),
                    "count_out": int(counter_zone.out_count)
                }
            else:
                return annotated, {
                    "count": int(counter_zone.current_count)
                }
        
        results, err = process_video(tmp_in_path, out_path, process_func)
        
        # Cleanup
        try:
            tmp_in_path.unlink()
        except:
            pass
        
        if err:
            return jsonify({"error": err}), 500
        
        response = {
            "type": "video",
            "video_url": f"/video/{out_path.name}",
            "frames_processed": results.get("frames_processed", 0),
            "enhancement_applied": enhance,
            "region_type": region_type,
            "tracker": tracker_cfg
        }
        
        if region_type == "line":
            response.update({
                "count_in": results.get("count_in", 0),
                "count_out": results.get("count_out", 0)
            })
        else:
            response.update({
                "count": results.get("count", 0)
            })
        
        return jsonify(response)
    
    else:
        # Process image
        img, err = read_image_from_request("file")
        if err:
            return jsonify({"error": err}), 400
        
        # Apply enhancement
        proc = img.copy()
        if enhance:
            proc = apply_enhancement(proc, enhancement_kind, brightness, contrast)
        
        # Track objects
        detections = run_tracking(model, proc, tracker_cfg=tracker_cfg)
        
        # Trigger counting
        counter_zone.trigger(detections=detections)
        
        # Annotate
        annotated = box_annotator.annotate(scene=proc, detections=detections)
        
        # Labels
        labels = []
        tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)
        for cid, conf, tid in zip(detections.class_id, detections.confidence, tracker_ids):
            if tid is not None:
                labels.append(f"#{tid} {model.names[cid]} {conf:0.2f}")
            else:
                labels.append(f"{model.names[cid]} {conf:0.2f}")
        
        annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        
        # Annotate counting zone
        if region_type == "line":
            zone_annotator.annotate(frame=annotated, line_counter=counter_zone)
        else:
            zone_annotator.annotate(frame=annotated, zone=counter_zone)
        
        response = {
            "type": "image",
            "image": image_to_base64(annotated),
            "enhancement_applied": enhance,
            "region_type": region_type,
            "tracker": tracker_cfg
        }
        
        if region_type == "line":
            response.update({
                "count_in": int(counter_zone.in_count),
                "count_out": int(counter_zone.out_count)
            })
        else:
            response.update({
                "count": int(counter_zone.current_count)
            })
        
        return jsonify(response)

# ============================================================================
# POLYGON MANAGEMENT
# ============================================================================

@app.route("/polygon/create", methods=["POST"])
def create_polygon():
    """
    Create a polygon zone for counting
    JSON body:
    - points: array of [x, y] coordinates
    Example: {"points": [[100, 100], [200, 100], [200, 200], [100, 200]]}
    """
    data = request.get_json(force=True)
    points = data.get("points")
    if not points or not isinstance(points, list):
        return jsonify({"error": "points must be list of [x,y] pairs"}), 400
    
    try:
        points_array = np.array(points, dtype=np.int32)
        poly, annot = create_polygon_zone(points_array)
        pid = uuid.uuid4().hex
        POLYGON_ZONES[pid] = (poly, annot)
        return jsonify({
            "polygon_id": pid,
            "message": "Polygon created successfully"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create polygon: {str(e)}"}), 400

@app.route("/polygon/list", methods=["GET"])
def list_polygons():
    """List all created polygon zones"""
    return jsonify({
        "polygons": list(POLYGON_ZONES.keys()),
        "total": len(POLYGON_ZONES)
    })

@app.route("/polygon/delete/<polygon_id>", methods=["DELETE"])
def delete_polygon(polygon_id):
    """Delete a polygon zone"""
    if polygon_id in POLYGON_ZONES:
        del POLYGON_ZONES[polygon_id]
        return jsonify({"message": "Polygon deleted successfully"})
    return jsonify({"error": "polygon_id not found"}), 404

# ============================================================================
# FILE MANAGEMENT
# ============================================================================

@app.route("/video/<filename>", methods=["GET"])
def serve_video(filename):
    """Serve processed video files"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "file not found"}), 404
    
    return send_file(
        str(file_path),
        mimetype='video/mp4',
        as_attachment=False,
        download_name=filename
    )

@app.route("/outputs", methods=["GET"])
def list_outputs():
    """List all output files"""
    files = [str(p.name) for p in OUTPUT_DIR.glob("*") if p.is_file()]
    return jsonify({"files": files, "total": len(files)})

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download a specific output file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "file not found"}), 404
    
    return send_file(str(file_path), as_attachment=True)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """API health check"""
    return jsonify({
        "status": "ok",
        "endpoints": {
            "detect": "/detect",
            "track": "/track",
            "count": "/count",
            "polygon_create": "/polygon/create",
            "polygon_list": "/polygon/list",
            "polygon_delete": "/polygon/delete/<id>"
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
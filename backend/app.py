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

def create_default_polygon(image_shape):
    """Create a default polygon covering the center 80% of the image"""
    h, w = image_shape[:2]
    margin_x = int(w * 0.1)
    margin_y = int(h * 0.1)
    
    points = [
        [margin_x, margin_y],
        [w - margin_x, margin_y],
        [w - margin_x, h - margin_y],
        [margin_x, h - margin_y]
    ]
    
    points_array = np.array(points, dtype=np.int32)
    poly, annot = create_polygon_zone(points_array)
    pid = uuid.uuid4().hex
    POLYGON_ZONES[pid] = (poly, annot)
    return pid, points

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
    Count objects inside polygon area
    Form params:
    - file: image or video file
    - enhance: true/false (optional, default: false)
    - enhancement_kind: CLAHE/histogram/gamma (optional, default: CLAHE)
    - brightness: int (optional, default: 0)
    - contrast: int (optional, default: 0)
    - tracker: bytetrack.yaml/botsort.yaml (optional, default: bytetrack.yaml)
    - polygon_id: optional - if provided, use existing polygon; if not, auto-generate
    """
    if "file" not in request.files:
        return jsonify({"error": "file not found"}), 400
    
    file = request.files["file"]
    polygon_id = request.form.get("polygon_id", None)
    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    
    # Get polygon zone - either use existing or create a new one
    polygon_points = None
    auto_generated = False
    
    if polygon_id and polygon_id in POLYGON_ZONES:
        # Use existing polygon
        poly_zone, poly_annot = POLYGON_ZONES[polygon_id]
    else:
        # Need to create a new polygon, but we need image dimensions first
        # Read the first frame to get dimensions
        if is_video_file(file):
            # Save temporarily to get dimensions
            tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
            file.save(str(tmp_in_path))
            
            cap = cv2.VideoCapture(str(tmp_in_path))
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                try:
                    tmp_in_path.unlink()
                except:
                    pass
                return jsonify({"error": "Failed to read video"}), 400
            
            # Create default polygon based on video dimensions
            polygon_id, polygon_points = create_default_polygon(frame.shape)
            poly_zone, poly_annot = POLYGON_ZONES[polygon_id]
            auto_generated = True
        else:
            # Read image to get dimensions
            img, err = read_image_from_request("file")
            if err:
                return jsonify({"error": err}), 400
            
            # Create default polygon based on image dimensions
            polygon_id, polygon_points = create_default_polygon(img.shape)
            poly_zone, poly_annot = POLYGON_ZONES[polygon_id]
            auto_generated = True
    
    # Check if video or image
    if is_video_file(file):
        # Process video
        if not auto_generated:  # If we didn't already save the video
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
            
            # Trigger counting in polygon
            poly_zone.trigger(detections=detections)
            
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
            
            # Annotate polygon zone
            poly_annot.annotate(frame=annotated, zone=poly_zone)
            
            # Return count
            return annotated, {
                "count": int(poly_zone.current_count)
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
            "polygon_id": polygon_id,
            "tracker": tracker_cfg,
            "count": results.get("count", 0),
            "auto_generated_polygon": auto_generated
        }
        
        if auto_generated and polygon_points:
            response["polygon_points"] = polygon_points
        
        return jsonify(response)
    
    else:
        # Process image
        if not auto_generated:  # If we didn't already read the image
            img, err = read_image_from_request("file")
            if err:
                return jsonify({"error": err}), 400
        
        # Apply enhancement
        proc = img.copy()
        if enhance:
            proc = apply_enhancement(proc, enhancement_kind, brightness, contrast)
        
        # Track objects
        detections = run_tracking(model, proc, tracker_cfg=tracker_cfg)
        
        # Trigger counting in polygon
        poly_zone.trigger(detections=detections)
        
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
        
        # Annotate polygon zone
        poly_annot.annotate(frame=annotated, zone=poly_zone)
        
        response = {
            "type": "image",
            "image": image_to_base64(annotated),
            "enhancement_applied": enhance,
            "polygon_id": polygon_id,
            "tracker": tracker_cfg,
            "count": int(poly_zone.current_count),
            "auto_generated_polygon": auto_generated
        }
        
        if auto_generated and polygon_points:
            response["polygon_points"] = polygon_points
        
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
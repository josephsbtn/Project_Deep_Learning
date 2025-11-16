# app.py
import os
import uuid
from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
from pathlib import Path
from models.yolo import model
from utils.enhancement import apply_enhancement
from utils.tracking import run_tracking
from utils.region import create_line_zone, create_polygon_zone, box_annotator, label_annotator

app = Flask(__name__)
OUTPUT_DIR = Path("static/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def read_image_from_request(field_name="file"):
    if field_name not in request.files:
        return None, "file not found"
    f = request.files[field_name]
    data = f.read()
    npimg = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    return img, None

# --- Endpoint Enhancement (multi-kind) ---
@app.route("/enhance-image", methods=["POST"])
def enhance_image():
    img, err = read_image_from_request("file")
    if err: return jsonify({"error": err}), 400

    kind = request.form.get("kind", "CLAHE")  # CLAHE, HE, BRIGHTNESS, CS
    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))
    enhanced = apply_enhancement(img, kind, brightness=brightness, contrast=contrast)

    out_path = OUTPUT_DIR / f"enhanced_{kind.lower()}_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(out_path), enhanced)
    return jsonify({"path": str(out_path)})

# --- Endpoint Detect Only ---
@app.route("/detect", methods=["POST"])
def detect_only():
    img, err = read_image_from_request("file")
    if err: return jsonify({"error": err}), 400

    results = model(img)[0]  # forward
    annotated = results.plot()  # numpy image
    out_path = OUTPUT_DIR / f"detect_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(out_path), annotated)
    # Also return raw detections
    detections_list = []
    for box, cls, conf in zip(results.boxes.xyxy.tolist(), results.boxes.cls.tolist(), results.boxes.conf.tolist()):
        detections_list.append({
            "box": box, "class_id": int(cls), "confidence": float(conf), "label": model.names[int(cls)]
        })
    return jsonify({"path": str(out_path), "detections": detections_list})

# --- Endpoint Tracking Only ---
@app.route("/track", methods=["POST"])
def track_only():
    img, err = read_image_from_request("file")
    if err: return jsonify({"error": err}), 400

    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    labels = [f"#{tid} {model.names[cid]} {conf:0.2f}" if detections.tracker_id is not None else f"{model.names[cid]} {conf:0.2f}"
              for cid, conf, tid in zip(detections.class_id, detections.confidence, detections.tracker_id if detections.tracker_id is not None else [None]*len(detections))]
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

    out_path = OUTPUT_DIR / f"track_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(out_path), annotated)
    return jsonify({"path": str(out_path), "num_detections": len(detections)})

# --- Endpoint Line Counting (tracking + line zone) ---
# Note: line_counter persists counts in memory; for production gunakan DB or reset logic per-session.
LINE_ZONE, LINE_ANNOTATOR = create_line_zone()

@app.route("/count-line", methods=["POST"])
def count_line():
    img, err = read_image_from_request("file")
    if err: return jsonify({"error": err}), 400
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    # trigger counting
    LINE_ZONE.trigger(detections=detections)

    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    labels = [f"#{tid} {model.names[cid]} {conf:0.2f}" if detections.tracker_id is not None else f"{model.names[cid]} {conf:0.2f}"
              for cid, conf, tid in zip(detections.class_id, detections.confidence, detections.tracker_id if detections.tracker_id is not None else [None]*len(detections))]
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    LINE_ANNOTATOR.annotate(frame=annotated, line_counter=LINE_ZONE)

    out_path = OUTPUT_DIR / f"count_line_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(out_path), annotated)
    return jsonify({
        "path": str(out_path),
        "count_in": LINE_ZONE.in_count,
        "count_out": LINE_ZONE.out_count
    })

# --- Endpoint Polygon Counter ---
# Accepts json body: {"points": [[x1,y1],[x2,y2],...]}
POLYGON_ZONES = {}  # in-memory store: polygon_id -> (zone, annotator)
@app.route("/create-polygon", methods=["POST"])
def create_polygon():
    data = request.get_json(force=True)
    points = data.get("points")
    if not points or not isinstance(points, list):
        return jsonify({"error":"points must be list of [x,y] pairs"}), 400
    poly, annot = create_polygon_zone(points)
    pid = uuid.uuid4().hex
    POLYGON_ZONES[pid] = (poly, annot)
    return jsonify({"polygon_id": pid})

@app.route("/count-polygon/<polygon_id>", methods=["POST"])
def count_polygon(polygon_id):
    if polygon_id not in POLYGON_ZONES:
        return jsonify({"error":"polygon_id not found"}), 404
    poly, annot = POLYGON_ZONES[polygon_id]
    img, err = read_image_from_request("file")
    if err: return jsonify({"error": err}), 400
    tracker_cfg = request.form.get("tracker", "bytetrack.yaml")
    detections = run_tracking(model, img, tracker_cfg=tracker_cfg)
    poly.trigger(detections=detections)  # update counts

    annotated = box_annotator.annotate(scene=img.copy(), detections=detections)
    labels = [f"#{tid} {model.names[cid]} {conf:0.2f}" if detections.tracker_id is not None else f"{model.names[cid]} {conf:0.2f}"
              for cid, conf, tid in zip(detections.class_id, detections.confidence, detections.tracker_id if detections.tracker_id is not None else [None]*len(detections))]
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    annot.annotate(frame=annotated, polygon=poly)

    out_path = OUTPUT_DIR / f"count_polygon_{polygon_id}_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(out_path), annotated)
    return jsonify({
        "path": str(out_path),
        "count_in": poly.in_count,
        "count_out": poly.out_count
    })

# --- Endpoint Process Video (pipeline) ---
# POST multi-part form:
# - file: video
# - enhance: true/false
# - enhancement_kind: CLAHE/HE/BRIGHTNESS/CS
# - track: true/false
# - count_mode: none/line/polygon
# - polygon_id (optional if polygon)
@app.route("/process-video", methods=["POST"])
def process_video():
    # WARNING: synchronous blocking call (CPU/GPU heavy)
    video_file = request.files.get("file")
    if video_file is None:
        return jsonify({"error":"file not provided"}), 400

    # read options
    enhance = request.form.get("enhance", "false").lower() == "true"
    enhancement_kind = request.form.get("enhancement_kind", "CLAHE")
    do_track = request.form.get("track", "false").lower() == "true"
    count_mode = request.form.get("count_mode", "none")  # none, line, polygon
    polygon_id = request.form.get("polygon_id", None)

    # save uploaded temporarily
    tmp_in_path = OUTPUT_DIR / f"tmp_in_{uuid.uuid4().hex}.mp4"
    video_file.save(str(tmp_in_path))

    cap = cv2.VideoCapture(str(tmp_in_path))
    if not cap.isOpened():
        return jsonify({"error":"gagal buka video"}), 500

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_path = OUTPUT_DIR / f"proc_{uuid.uuid4().hex}.mp4"
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w,h))

    # prepare counters if requested
    line_zone = None
    line_annot = None
    poly_zone = None
    poly_annot = None
    if count_mode == "line":
        line_zone, line_annot = create_line_zone()
    elif count_mode == "polygon":
        if not polygon_id or polygon_id not in POLYGON_ZONES:
            cap.release(); writer.release()
            return jsonify({"error":"polygon_id invalid or not provided"}), 400
        poly_zone, poly_annot = POLYGON_ZONES[polygon_id]

    # loop frames
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
            labels = [f"#{tid} {model.names[cid]} {conf:0.2f}" if det.tracker_id is not None else f"{model.names[cid]} {conf:0.2f}"
                      for cid, conf, tid in zip(det.class_id, det.confidence, det.tracker_id if det.tracker_id is not None else [None]*len(det))]
            proc = label_annotator.annotate(proc, det, labels)

            if count_mode == "line" and line_zone is not None:
                line_zone.trigger(detections=det)
                line_annot.annotate(frame=proc, line_counter=line_zone)
            if count_mode == "polygon" and poly_zone is not None:
                poly_zone.trigger(detections=det)
                poly_annot.annotate(frame=proc, polygon=poly_zone)

        # write frame
        writer.write(proc)
        frame_idx += 1

    cap.release()
    writer.release()
    try:
        tmp_in_path.unlink()
    except:
        pass

    result = {"path": str(out_path)}
    if line_zone:
        result.update({"count_in": line_zone.in_count, "count_out": line_zone.out_count})
    if poly_zone:
        result.update({"count_in": poly_zone.in_count, "count_out": poly_zone.out_count})
    return jsonify(result)

@app.route("/outputs", methods=["GET"])
def list_outputs():
    files = [str(p) for p in OUTPUT_DIR.glob("*")]
    return jsonify({"files": files})

@app.route("/download", methods=["GET"])
def download_file():
    path = request.args.get("path")
    if not path: return jsonify({"error":"path param required"}), 400
    p = Path(path)
    if not p.exists(): return jsonify({"error":"file not found"}), 404
    return send_file(str(p), as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

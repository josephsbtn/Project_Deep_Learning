# utils/tracking.py
import supervision as sv

def run_tracking(model, frame, tracker_cfg="bytetrack.yaml", persist=True, verbose=False):
    """
    Mengembalikan object detections (sv.Detections) dari hasil model.track
    """
    results = model.track(frame, persist=persist, tracker=tracker_cfg, verbose=verbose)
    det = sv.Detections.from_ultralytics(results[0])
    return det

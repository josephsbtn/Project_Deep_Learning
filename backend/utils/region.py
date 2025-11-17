import supervision as sv
import numpy as np

# Default Line (sesuaikan dengan resolusi video Anda)
DEFAULT_LINE_START = sv.Point(0, 360)
DEFAULT_LINE_END = sv.Point(1280, 360)

def create_line_zone(start=DEFAULT_LINE_START, end=DEFAULT_LINE_END):
    """
    Membuat LineZone dan annotator untuk counting objek yang melewati garis
    """
    line_zone = sv.LineZone(start=start, end=end)
    annotator = sv.LineZoneAnnotator(thickness=2)
    return line_zone, annotator

def create_polygon_zone(points):
    """
    Membuat PolygonZone dan annotator
    
    Args:
        points: numpy array dengan shape (n, 2) atau list of [x, y] pairs
    
    Returns:
        tuple: (PolygonZone, PolygonZoneAnnotator)
    """
    # Pastikan points dalam format numpy array
    if not isinstance(points, np.ndarray):
        points = np.array(points, dtype=np.int32)
    
    # PolygonZone membutuhkan numpy array dengan shape (n, 2)
    if len(points.shape) != 2 or points.shape[1] != 2:
        raise ValueError("Points must be a 2D array with shape (n, 2)")
    
    poly = sv.PolygonZone(polygon=points)
    annotator = sv.PolygonZoneAnnotator(
        thickness=2,
        text_thickness=2,
        text_scale=1
    )
    return poly, annotator

# Shared annotators untuk boxes & labels
box_annotator = sv.BoxAnnotator(thickness=2)
label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)
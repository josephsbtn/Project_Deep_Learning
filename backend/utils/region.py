# utils/region.py
import supervision as sv

# Default Line (ubah sesuai resolusi videomu)
DEFAULT_LINE_START = sv.Point(0, 360)
DEFAULT_LINE_END = sv.Point(1280, 360)

def create_line_zone(start=DEFAULT_LINE_START, end=DEFAULT_LINE_END):
    line_zone = sv.LineZone(start=start, end=end)
    annotator = sv.LineZoneAnnotator(thickness=2)
    return line_zone, annotator

def create_polygon_zone(points):
    """
    points: list of (x,y) tuples
    """ 
    poly = sv.PolygonZone(polygon=points)
    annotator = sv.PolygonZoneAnnotator()
    return poly, annotator

# Annotators for boxes & labels (shared)
box_annotator = sv.BoxAnnotator(thickness=2)
label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)

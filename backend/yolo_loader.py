import os
from ultralytics import YOLO

_model = None

def get_yolo_model():
    global _model
    if _model is not None:
        return _model

    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "..", "model", "best.pt")
    
    if not os.path.isfile(path):
        print(f"⚠️ YOLO weights not found at {path}.")
        return None

    _model = YOLO(path)
    return _model

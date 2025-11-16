from ultralytics import YOLO
import numpy as np
import torch

# Load model once and move to GPU if available. Use FP16 on CUDA for speed.
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL_PATH = "yolov8m.pt"

try:
    model = YOLO(_MODEL_PATH)
    # move underlying model to device where supported
    if _DEVICE == "cuda":
        try:
            model.model.to('cuda')
        except Exception:
            pass
except Exception as e:
    # lazy fallback if model fails to load here
    model = None
    print(f"[yolo_inference] Failed to load model '{_MODEL_PATH}': {e}")


def run_yolo_inference(frame: np.ndarray, imgsz: int = 640, conf_thresh: float = 0.2):
    """
    Runs YOLOv8 inference on a single frame and returns only 'person' detections.

    Args:
        frame (np.ndarray): The input image/frame (BGR, as from OpenCV).
        imgsz (int): Inference image size (max dimension); model will be given this size.

    Returns:
        dict: {"boxes": [[x1,y1,x2,y2],...], "confidences": [...], "class_ids": [...], "class_names": [...]}
    """
    global model
    if model is None:
        raise RuntimeError("YOLO model is not loaded")

    # ultralytics accepts BGR numpy arrays; pass device and half flag
    half_flag = True if _DEVICE == "cuda" else False

    # Call model with resized imgsz for faster inference
    results = model(frame, device=_DEVICE, imgsz=imgsz, half=half_flag)

    boxes = []
    confidences = []
    class_ids = []
    class_names = []

    r = results[0]
    # r.boxes may be empty
    for b in getattr(r, 'boxes', []):
        try:
            cls = int(b.cls[0])
            name = model.names[cls]
            # filter for person only to reduce downstream work
            if name != 'person':
                continue
            xyxy = [float(x) for x in b.xyxy[0]]
            conf = float(b.conf[0])
            boxes.append(xyxy)
            confidences.append(conf)
            class_ids.append(cls)
            class_names.append(name)
        except Exception:
            continue

    return {
        "boxes": boxes,
        "confidences": confidences,
        "class_ids": class_ids,
        "class_names": class_names,
    }
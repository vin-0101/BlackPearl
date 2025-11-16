"""
FastAPI video server that runs the socket receiver + YOLO processing in the background
and exposes:
 - GET /video_feed -> MJPEG stream of annotated frames
 - GET /logs -> recent log entries (simple in-memory log)

Run with:
    uvicorn gcs_backend.video.video_server:app --host 0.0.0.0 --port 8000

This file integrates the existing receiver/YOLO logic and provides an easy way for
`gcs_frontend_new` to consume the processed frames at http://localhost:8000/video_feed
"""

import threading
import time
import socket
import io
import cv2
import av
import queue
from typing import List, Dict, Any
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add repo root imports
import os, sys
_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
# Also make the current video directory importable so local modules like
# `yolo_inference.py` can be imported with a plain `from yolo_inference import ...`.
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from yolo_inference import run_yolo_inference
# optional local stream adapter (for testing with webcam or video files)
try:
    from local_stream import start_local_stream
except Exception:
    start_local_stream = None

app = FastAPI()

# Allow cross-origin requests from the frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration (fixed for RPi stream)
SENDER_IP = '192.168.50.1'
PORT = 8888
FRAME_QUEUE_SIZE = 60
RUN_INFERENCE_EVERY_N = 1
INFERENCE_WIDTH = 640
DISPLAY_FPS = 10
SOCKET_RCVBUF = 4 * 1024 * 1024

# Shared state
frame_queue = queue.Queue(maxsize=FRAME_QUEUE_SIZE)
latest_frame_jpg = None
latest_frame_lock = threading.Lock()
stop_event = threading.Event()
receiver_connected = False
logs: List[Dict[str, Any]] = []


def log(msg: str, level: str = 'info'):
    entry = {'timestamp': time.time(), 'level': level, 'message': msg}
    logs.append(entry)
    # keep log size bounded
    if len(logs) > 500:
        del logs[0]
    print(msg)


# Receiver thread
def receiver_thread():
    # expose status flag from this thread
    global receiver_connected

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_RCVBUF)
        sock.settimeout(10)
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                sock.connect((SENDER_IP, PORT))
                # mark receiver connected (used by /status)
                receiver_connected = True
                log(f"[Receiver] Connected to sender at {SENDER_IP}:{PORT} (attempt {attempt})")
                break
            except socket.timeout:
                log(f"[Receiver] Connection attempt {attempt} timed out", 'warning')
            except Exception as e:
                log(f"[Receiver] Connection attempt {attempt} failed: {e}", 'warning')
            if attempt < max_retries:
                time.sleep(1.0)
        else:
            log("[Receiver] Failed to connect after retries", 'error')
            return

        sock_file = sock.makefile('rb')
        container = av.open(sock_file, format='mpegts')

        for frame in container.decode(video=0):
            if stop_event.is_set():
                break
            try:
                img = frame.to_ndarray(format='bgr24')
            except Exception as e:
                log(f"[Receiver] frame conversion error: {e}", 'warning')
                continue
            timestamp = time.time()
            try:
                frame_queue.put_nowait((img, timestamp))
            except queue.Full:
                try:
                    _ = frame_queue.get_nowait()
                    frame_queue.put_nowait((img, timestamp))
                except queue.Full:
                    pass
    except Exception as e:
        log(f"[Receiver] Error: {e}", 'error')
        # on any error, mark disconnected
        try:
            receiver_connected = False
        except Exception:
            pass
    finally:
        try:
            sock.close()
        except Exception:
            pass
        # ensure status cleared when thread exits
        try:
            receiver_connected = False
        except Exception:
            pass
        log("[Receiver] Receiver thread exiting")


# Processing thread: pulls frames, runs YOLO, draws boxes, updates latest_frame_jpg
def processing_thread():
    frame_count = 0
    prev_time = time.time()
    infer_counter = 0
    last_display = 0

    while not stop_event.is_set():
        try:
            img, recv_time = frame_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        frame_count += 1
        now = time.time()

        # decide whether to run inference on this frame
        run_inference = (infer_counter % RUN_INFERENCE_EVERY_N == 0)
        infer_counter += 1

        detections = {"boxes": [], "confidences": [], "class_ids": [], "class_names": []}

        if run_inference:
            h, w = img.shape[:2]
            scale = 1.0
            if max(w, h) > INFERENCE_WIDTH:
                scale = INFERENCE_WIDTH / float(max(w, h))
                new_w = int(w * scale)
                new_h = int(h * scale)
                img_small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            else:
                img_small = img

            try:
                detections = run_yolo_inference(img_small)
            except Exception as e:
                log(f"[Processor] YOLO inference error: {e}", 'error')
                detections = {"boxes": [], "confidences": [], "class_ids": [], "class_names": []}

            # scale boxes back to original coordinates if resized
            if scale != 1.0 and detections.get("boxes"):
                scaled_boxes = []
                for box in detections["boxes"]:
                    x1 = int(box[0] / scale)
                    y1 = int(box[1] / scale)
                    x2 = int(box[2] / scale)
                    y2 = int(box[3] / scale)
                    scaled_boxes.append([x1, y1, x2, y2])
                detections["boxes"] = scaled_boxes

        # draw detections (only persons)
        person_count = 0
        if detections and detections.get("boxes"):
            for box, cls_name, conf in zip(detections["boxes"], detections["class_names"], detections["confidences"]):
                if cls_name != "person":
                    continue
                person_count += 1
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{cls_name} {conf:.2f}"
                cv2.putText(img, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # draw info box: resolution, fps, latency, detections count
        height, width = img.shape[:2]
        latency_ms = (time.time() - recv_time) * 1000

        box_x, box_y, box_w, box_h = 10, 10, 380, 110
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), -1)
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 255, 0), 2)
        cv2.putText(img, f"Resolution: {width}x{height}", (box_x + 12, box_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(img, f"Persons: {person_count}", (box_x + 12, box_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(img, f"Latency: {latency_ms:.1f} ms", (box_x + 12, box_y + 82), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # encode to JPEG
        ret, jpg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ret:
            with latest_frame_lock:
                global latest_frame_jpg
                latest_frame_jpg = jpg.tobytes()

        # small sleep to avoid hogging CPU if upstream is very fast
        time.sleep(0.001)

    log('[Processor] Processing thread exiting')


@app.on_event('startup')
def start_workers():
    # Always start the RPi receiver and processor threads
    t_recv = threading.Thread(target=receiver_thread, daemon=True)
    t_proc = threading.Thread(target=processing_thread, daemon=True)
    t_recv.start()
    t_proc.start()
    log('[Server] Workers started')


@app.on_event('shutdown')
def stop_workers():
    stop_event.set()
    log('[Server] Shutdown requested')


def mjpeg_generator(boundary: str = 'frame'):
    # yields multipart/x-mixed-replace frames using latest_frame_jpg
    while not stop_event.is_set():
        with latest_frame_lock:
            img = latest_frame_jpg
        if img is None:
            # no frame yet; wait a bit
            time.sleep(0.05)
            continue
        # yield multipart chunk
        yield (b"--%b\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % (boundary.encode(), len(img))) + img + b"\r\n"
        time.sleep(1.0 / max(1, DISPLAY_FPS))


@app.get('/video_feed')
def video_feed():
    return StreamingResponse(mjpeg_generator(), media_type='multipart/x-mixed-replace; boundary=frame')


@app.get('/logs')
def get_logs():
    return JSONResponse(content=logs)


@app.get('/status')
def get_status():
    """Return simple health info useful to the frontend: whether receiver/local stream is connected and recent logs count."""
    try:
        rc = bool(receiver_connected)
    except Exception:
        rc = False
    return JSONResponse(content={
        'receiver_connected': rc,
        'log_count': len(logs)
    })


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('gcs_backend.video.video_server:app', host='0.0.0.0', port=8000, reload=False)

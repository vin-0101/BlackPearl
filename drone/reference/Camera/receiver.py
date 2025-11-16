import socket
import cv2
import av
import time
import threading
import queue

# ---------------------------
# Configuration
# ---------------------------
SENDER_IP = "192.168.50.1"
PORT = 8888
FRAME_QUEUE_SIZE = 60

frame_queue = queue.Queue(maxsize=FRAME_QUEUE_SIZE)

# ---------------------------
# Receiver Thread: decode frames
# ---------------------------
def receiver_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SENDER_IP, PORT))
    print(f"[Receiver] Connected to sender at {SENDER_IP}:{PORT}")

    sock_file = sock.makefile('rb')
    container = av.open(sock_file, format='mpegts')

    try:
        for frame in container.decode(video=0):
            img = frame.to_ndarray(format='bgr24')
            timestamp = time.time()
            if not frame_queue.full():
                frame_queue.put((img, timestamp))
    except Exception as e:
        print(f"[Receiver] Error: {e}")
    finally:
        sock.close()

# ---------------------------
# Main Thread: display frames
# ---------------------------
frame_count = 0
fps = 0
prev_time = time.time()

recv_thread = threading.Thread(target=receiver_thread, daemon=True)
recv_thread.start()

try:
    while True:
        if frame_queue.empty():
            time.sleep(0.001)
            continue

        img, recv_time = frame_queue.get()
        frame_count += 1

        # Resolution
        height, width = img.shape[:2]

        # FPS calculation every second
        current_time = time.time()
        if (current_time - prev_time) >= 1.0:
            fps = frame_count / (current_time - prev_time)
            frame_count = 0
            prev_time = current_time

        # Approximate latency
        latency_ms = (time.time() - recv_time) * 1000

        # Draw info box
        box_x, box_y = 10, 10
        box_w, box_h = 300, 90
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 0), -1)
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 255, 0), 2)

        text_y = box_y + 25
        cv2.putText(img, f"Resolution : {width}x{height}", (box_x + 10, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(img, f"FPS        : {fps:.2f}", (box_x + 10, text_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(img, f"Latency    : {latency_ms:.1f} ms", (box_x + 10, text_y + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Display in main thread
        cv2.imshow("RGB Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("[Receiver] Stopped by user")
finally:
    cv2.destroyAllWindows()

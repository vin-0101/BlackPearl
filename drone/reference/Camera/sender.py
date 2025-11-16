import socket
from threading import Event
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput

PORT = 8888

# Camera setup
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1280,720), "format": "YUV420"}
)
picam2.configure(video_config)

encoder = H264Encoder(bitrate=10000000)  # 10 Mbps
encoder.audio = False  # set True if you want audio

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))

    while True:
        print("[Sender] Waiting for receiver...")
        sock.listen(1)
        conn, addr = sock.accept()
        print(f"[Sender] Connected to {addr[0]}:{addr[1]}")

        output = PyavOutput(f"pipe:{conn.fileno()}", format="mpegts")
        event = Event()
        output.error_callback = lambda e: event.set()  # signals disconnect/error

        picam2.start_recording(encoder, output)
        event.wait()  # wait until connection closes / error occurs
        print("[Sender] Receiver disconnected")
        picam2.stop_recording()

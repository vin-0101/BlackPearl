import socket
from threading import Event, Thread
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput


class VideoStreamer:
    def __init__(self, port=8888, resolution=(1280, 720), bitrate=10_000_000):
        self.port = port
        self.resolution = resolution
        self.bitrate = bitrate

        self.picam2 = None
        self.encoder = None
        self.server_socket = None

        self.stop_event = Event()
        self.thread = None
        self.running = False

    # ---------------------------------------------
    # INIT CAMERA & SOCKET
    # ---------------------------------------------
    def _init_camera(self):
        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration(
            main={"size": self.resolution, "format": "YUV420"}
        )
        self.picam2.configure(video_config)

        self.encoder = H264Encoder(bitrate=self.bitrate)
        self.encoder.audio = False

    def _init_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))

    # ---------------------------------------------
    # STREAM ONE CLIENT
    # ---------------------------------------------
    def _stream_to_client(self, conn):
        print(f"[Streamer] Streaming to {conn.getpeername()}")

        output = PyavOutput(f"pipe:{conn.fileno()}", format="mpegts")
        disconnect_event = Event()
        output.error_callback = lambda e: disconnect_event.set()

        self.picam2.start_recording(self.encoder, output)

        try:
            while not self.stop_event.is_set() and not disconnect_event.is_set():
                self.stop_event.wait(0.1)
        finally:
            print("[Streamer] Stopping recording...")
            self.picam2.stop_recording()

    # ---------------------------------------------
    # ACCEPT CLIENTS FOREVER (UNTIL STOP EVENT)
    # ---------------------------------------------
    def _connection_loop(self):
        print(f"[Streamer] Ready on port {self.port}")
        self.server_socket.listen(1)

        while not self.stop_event.is_set():
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
            except socket.timeout:
                continue

            print(f"[Streamer] Connected to {addr[0]}:{addr[1]}")
            self._stream_to_client(conn)
            conn.close()
            print("[Streamer] Client disconnected. Waiting again...")

        print("[Streamer] Server stopped. Exiting loop.")

    # ---------------------------------------------
    # PUBLIC: START STREAMING
    # ---------------------------------------------
    def start(self):
        if self.running:
            print("[Streamer] Already running.")
            return

        print("[Streamer] Starting video streamer...")

        self.stop_event.clear()
        self._init_camera()
        self._init_socket()

        self.thread = Thread(target=self._connection_loop, daemon=True)
        self.thread.start()
        self.running = True

    # ---------------------------------------------
    # PUBLIC: STOP STREAMING
    # ---------------------------------------------
    def stop(self):
        if not self.running:
            print("[Streamer] Not running.")
            return

        print("[Streamer] Stopping streamer...")

        self.stop_event.set()

        if self.thread:
            self.thread.join()

        try:
            self.server_socket.close()
        except:
            pass

        try:
            self.picam2.close()
        except:
            pass

        self.running = False
        print("[Streamer] Stopped successfully.")

    # ---------------------------------------------
    # RESTART
    # ---------------------------------------------
    def restart(self):
        print("[Streamer] Restarting...")
        self.stop()
        self.start()

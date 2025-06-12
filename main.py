# -*- coding: utf-8 -*-
import asyncio
import websockets
import aiohttp
import json
import cv2
import qrcode
from PIL import ImageTk, Image
import tkinter as tk
from io import BytesIO
from picamera2 import Picamera2


# -------------------- GLOBAL STATE --------------------
qr_window = None  # Reference to the Tkinter window with the QR-code
TARGET_FPS = 60
FRAME_DELAY = 1.0 / TARGET_FPS
SERVER_WS_URL = "ws://192.168.31.79:8888/camera"
NEW_QR_URL = "http://147.45.163.58:8081/api/auth_camera/new_qr"
QR_REDIRECT_BASE = "http://hsmg.ru/Auth_Camera/"  # Used to build the URL encoded in the QR-code


# -------------------- QR-CODE HELPERS --------------------

def open_qr_window(token: str) -> None:
    """Show a window with a freshly generated QR-code and keep a global reference."""
    global qr_window

    # Close previous window (if it exists)
    close_qr_window()

    qr_data = f"{QR_REDIRECT_BASE}{token}"
    qr = qrcode.make(qr_data)

    img_bytes = BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)


    # IMPORTANT: Tk root must be created before instantiating PhotoImage
    qr_window = tk.Tk()
    qr_window.title("QR Code Scan to Authorise Camera")

    img_tk = ImageTk.PhotoImage(Image.open(img_bytes), master=qr_window)

    label = tk.Label(qr_window, image=img_tk)
    label.image = img_tk  # Prevent garbage-collection
    label.pack()

    # Render the first frame of the UI (non-blocking)
    qr_window.update()
    print("[INFO] QR-code displayed  waiting for the mobile app")


def close_qr_window() -> None:
    """Close the QR-code window if it is currently open."""
    global qr_window
    if qr_window is not None:
        qr_window.destroy()
        qr_window = None
        print("[INFO] QR-code window closed.")


# -------------------- CAMERA WRAPPER --------------------

class PiCameraCapture:
    """A minimal wrapper around PiCamera2 providing an OpenCV-style API."""

    def __init__(self) -> None:
        self.camera = Picamera2()
        config = self.camera.create_video_configuration(
            main={"size": (1920, 1080), "format": "RGB888"},
            controls={"FrameRate": TARGET_FPS},
        )
        self.camera.configure(config)
        self.camera.start(show_preview=False)
        print("[INFO] PiCamera2 started with target FPS:", TARGET_FPS)

    def read(self):
        frame = self.camera.capture_array()
        return True, frame

    def isOpened(self):
        return True  # Always true while the camera is active

    def release(self):
        self.camera.stop()
        self.camera.close()
        print("[INFO] Camera released.")


# -------------------- NETWORK HELPERS --------------------

async def fetch_new_token() -> str:
    """Request a new token from the backend that will be encoded inside the QR-code."""
    async with aiohttp.ClientSession() as session:
        async with session.get(NEW_QR_URL) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Unexpected status {resp.status} when requesting QR token")
            data = await resp.json()
            token = data.get("token") if isinstance(data, dict) else str(data)
            print("[INFO] Received new token:", token)
            return token
            


# -------------------- STREAMING LOGIC --------------------

async def stream_camera(ws: websockets.WebSocketClientProtocol) -> None:
    """Capture frames and push them through the open WebSocket connection until it closes."""
    camera = PiCameraCapture()
    try:
        while camera.isOpened():
            ret, frame = camera.read()
            if not ret:
                print("[WARNING] Failed to capture frame  stopping stream.")
                break

            # Encode frame as JPEG
            success, jpeg_frame = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                print("[WARNING] Failed to encode frame  skipping.")
                continue

            await ws.send(jpeg_frame.tobytes())
            cv2.imshow("Client  Live Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[INFO] Local quit signal  received  stopping stream.")
                break

            await asyncio.sleep(FRAME_DELAY)
    except websockets.exceptions.ConnectionClosed:
        print("[INFO] WebSocket closed by server  stream ended.")
    finally:
        camera.release()
        cv2.destroyAllWindows()


# -------------------- MAIN CLIENT LOOP --------------------

async def camera_client() -> None:
    """Main loop: request token ? wait for start_stream ? stream video ? repeat."""
    while True:
        try:
            token = await fetch_new_token()
        except Exception as exc:
            print(f"[ERROR] Failed to fetch token: {exc}. Retrying in 3 ")
            await asyncio.sleep(3)
            continue

        open_qr_window(token)

        try:
            async with websockets.connect(SERVER_WS_URL) as ws:
                await ws.send(json.dumps({"token": token}))
                print("[INFO] Token sent  awaiting instructions from server")

                # Wait for commands from server
                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                    except (TypeError, json.JSONDecodeError):
                        data = {}

                    command = data.get("command")
                    if command == "start_stream":
                        print("[INFO] Received start_stream beginning video upload.")
                        close_qr_window()
                        await stream_camera(ws)
                        break  # After streaming returns, break to fetch a new token
                    elif command == "stop_stream":
                        print("[INFO] Received stop_stream server requested to end transmission.")
                        break  # Server explicitly asked to stop (rare, as it will usually just close)
        except (ConnectionRefusedError, websockets.exceptions.InvalidURI) as exc:
            print(f"[ERROR] Could not connect to server: {exc}. Retrying in 3 s")
            await asyncio.sleep(3)
            continue
        except websockets.exceptions.ConnectionClosedError as exc:
            print(f"[INFO] Connection closed unexpectedly: {exc}. Restarting loop")
        finally:
            close_qr_window()
            cv2.destroyAllWindows()
            print("[INFO] Restarting main loop  waiting for new session\n")
            # Small delay to avoid tight reconnect loops
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(camera_client())
    except KeyboardInterrupt:
        print("[INFO] Keyboard interrupt received exiting application.") 

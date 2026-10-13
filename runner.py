import subprocess
import webbrowser
import time
import http.server
import socketserver
import threading
import sys

BACKEND_SCRIPT = "main.py"
FRONTEND_FILE = "frontend.html"
PORT = 8000

def start_server():
    """Spins up a local server to prevent CORS blocking on the LLM API"""
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        print(f"[SYSTEM] Frontend Matrix active at http://localhost:{PORT}/{FRONTEND_FILE}")
        httpd.serve_forever()

if __name__ == "__main__":
    print("[SYSTEM] Initiating Project Parker Boot Sequence...")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    print("[SYSTEM] Booting Optical Feed & YOLO Engine...")
    try:
        backend_process = subprocess.Popen([sys.executable, BACKEND_SCRIPT])
    except FileNotFoundError:
        print(f"[CRITICAL] Could not find {BACKEND_SCRIPT}. Check the filename.")
        sys.exit(1)

    time.sleep(3) 
    webbrowser.open(f"http://localhost:{PORT}/{FRONTEND_FILE}")

    print("[SYSTEM] All systems nominal. Press Ctrl+C to terminate.")

    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown command received. Terminating processes...")
        backend_process.terminate()
        print("[SYSTEM] Grid offline.")
        sys.exit(0)

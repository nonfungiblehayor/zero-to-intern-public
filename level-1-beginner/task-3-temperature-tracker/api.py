"""
api.py - WeatherStation Temperature Analyzer Backend Bridge
Provides JSON endpoints for both FastAPI and Python's built-in HTTP server.
"""

import sys
import os
import json

# Ensure src/ is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from temperature_analyzer import analyze_temperatures

PORT = 8000

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from typing import List, Optional

    app = FastAPI(title="Temperature Analyzer API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class TemperatureRequest(BaseModel):
        readings: List[float] = Field(default_factory=list)

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "app": "temperature-tracker", "engine": "FastAPI"}

    @app.post("/api/temperature/analyze")
    def analyze_endpoint(payload: TemperatureRequest):
        try:
            stats = analyze_temperatures(payload.readings)
            return {"success": True, "stats": stats}
        except ZeroDivisionError as e:
            raise HTTPException(status_code=500, detail="ZeroDivisionError: list is empty (starter bug).")
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    def run_server():
        import uvicorn
        print(f"🚀 Temperature Analyzer FastAPI server starting on http://localhost:{PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)

except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class FallbackRequestHandler(BaseHTTPRequestHandler):
        def _send_cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self):
            self.send_response(204)
            self._send_cors_headers()
            self.end_headers()

        def do_GET(self):
            if self.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "app": "temperature-tracker", "engine": "Builtin-HTTPServer"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/api/temperature/analyze":
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                try:
                    payload = json.loads(body)
                    readings = payload.get("readings", [])
                    stats = analyze_temperatures(readings)
                    response_data = {"success": True, "stats": stats}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                except ZeroDivisionError as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "ZeroDivisionError: list is empty (starter bug)."}).encode())
                except (ValueError, TypeError) as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": str(e)}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": f"Internal Server Error: {str(e)}"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    def run_server():
        server = HTTPServer(("0.0.0.0", PORT), FallbackRequestHandler)
        print(f"🚀 Temperature Analyzer Standard HTTP server starting on http://localhost:{PORT}")
        print("💡 Hint: Run `pip install -r requirements.txt` for live reload FastAPI server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()

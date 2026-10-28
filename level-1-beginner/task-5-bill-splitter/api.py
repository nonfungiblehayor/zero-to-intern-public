import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from bill_splitter import calculate_split

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Any
    import uvicorn
    USE_FASTAPI = True
except ImportError:
    USE_FASTAPI = False

if USE_FASTAPI:
    app = FastAPI(title="QuickSplit Dining Bill Calculator API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class SplitRequest(BaseModel):
        total_bill: Any
        num_people: Any
        tip_percent: Any = 15

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "QuickSplit Bill Calculator"}

    @app.post("/api/bill/split")
    def split_bill(req: SplitRequest):
        try:
            return calculate_split(req.total_bill, req.num_people, req.tip_percent)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def run_server():
        print("Starting FastAPI server on http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)

else:
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            if self.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "service": "QuickSplit Bill Calculator"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/api/bill/split":
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode())
                try:
                    res = calculate_split(
                        body.get("total_bill"),
                        body.get("num_people"),
                        body.get("tip_percent", 15)
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode())
                except Exception as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": str(e)}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    def run_server():
        print("Starting API Server on http://localhost:8000 (Standard Library HTTP Engine)")
        server = HTTPServer(("0.0.0.0", 8000), SimpleHandler)
        server.serve_forever()


if __name__ == "__main__":
    run_server()

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from grade_calculator import calculate_grade_report, assign_letter_grade

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    USE_FASTAPI = True
except ImportError:
    USE_FASTAPI = False

if USE_FASTAPI:
    app = FastAPI(title="EduGrade Grade Calculator API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class GradeRequest(BaseModel):
        student_name: str
        score: float
        has_extra_credit: bool = False

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "EduGrade Grade Calculator"}

    @app.post("/api/grade/calculate")
    def calculate(req: GradeRequest):
        try:
            return calculate_grade_report(req.student_name, req.score, req.has_extra_credit)
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
                self.wfile.write(json.dumps({"status": "ok", "service": "EduGrade Grade Calculator"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/api/grade/calculate":
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode())
                try:
                    res = calculate_grade_report(
                        body.get("student_name", "Student"),
                        float(body.get("score", 0)),
                        bool(body.get("has_extra_credit", False))
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
            # Suppress noisy request logging
            pass

    def run_server():
        print("Starting API Server on http://localhost:8000 (Standard Library HTTP Engine)")
        server = HTTPServer(("0.0.0.0", 8000), SimpleHandler)
        server.serve_forever()


if __name__ == "__main__":
    run_server()

#!/usr/bin/env python3
"""
CloudGate API Gateway - Rate Limiter Backend Service
Dual-mode server: Runs FastAPI if installed, falls back to Python stdlib http.server.
"""

import sys
import os
import json
from typing import Optional, List, Dict, Any

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models import RateLimitConfig, ClientRequest, RateLimitResult
from clock import TestClock
from storage import SlidingWindowStore
from limiter import SlidingWindowRateLimiter
from gateway import APIGateway

# Initialize in-memory Gateway & Rate Limiter with TestClock
clock = TestClock(start_time=1000.0)
store = SlidingWindowStore()
config = RateLimitConfig(limit=10, window_seconds=60.0)
limiter = SlidingWindowRateLimiter(config, store, clock)
gateway = APIGateway(limiter)

# Pre-populate demo client
gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now()))
gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now() + 5.0))


def get_current_state() -> Dict[str, Any]:
    now = clock.now()
    clients = {}
    for cid, data in store._data.items():
        time_into_curr = max(0.0, now - data.current_window_start)
        # Calculate theoretical weight and estimate for visualization
        decay = max(0.0, min(1.0, 1.0 - (time_into_curr / config.window_seconds)))
        est = (data.previous_window_count * decay) + data.current_window_count
        clients[cid] = {
            "previous_window_count": data.previous_window_count,
            "current_window_count": data.current_window_count,
            "current_window_start": round(data.current_window_start, 2),
            "time_into_current": round(time_into_curr, 2),
            "decay_weight": round(decay, 4),
            "estimated_count": round(est, 2),
            "limit": config.limit,
            "window_seconds": config.window_seconds
        }

    return {
        "clock_time": round(now, 2),
        "config": {
            "limit": config.limit,
            "window_seconds": config.window_seconds
        },
        "active_clients_count": len(clients),
        "clients": clients
    }


# Try FastAPI first
try:
    from fastapi import FastAPI, HTTPException, Body
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel

    app = FastAPI(title="CloudGate API Gateway Rate Limiter API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class RequestPayload(BaseModel):
        client_id: str
        endpoint: Optional[str] = "/api/resource"

    class BurstPayload(BaseModel):
        client_id: str
        count: int = 5
        endpoint: Optional[str] = "/api/resource"

    class AdvanceClockPayload(BaseModel):
        seconds: float = 10.0

    class SetClockPayload(BaseModel):
        timestamp: float

    class ConfigPayload(BaseModel):
        limit: int = 10
        window_seconds: float = 60.0

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "CloudGate Rate Limiter Gateway"}

    @app.get("/api/state")
    def state():
        return get_current_state()

    @app.post("/api/request")
    def handle_request(payload: RequestPayload):
        try:
            status_code, headers, body = gateway.handle_request(
                ClientRequest(payload.client_id, payload.endpoint, clock.now())
            )
            return {
                "status_code": status_code,
                "headers": headers,
                "body": body,
                "clock_time": round(clock.now(), 2)
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/burst")
    def handle_burst(payload: BurstPayload):
        if payload.count <= 0 or payload.count > 100:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
        
        results = []
        allowed_count = 0
        blocked_count = 0

        for _ in range(payload.count):
            status_code, headers, body = gateway.handle_request(
                ClientRequest(payload.client_id, payload.endpoint, clock.now())
            )
            if status_code == 200:
                allowed_count += 1
            else:
                blocked_count += 1
            results.append({
                "status_code": status_code,
                "headers": headers,
                "body": body
            })

        return {
            "client_id": payload.client_id,
            "total_requested": payload.count,
            "allowed": allowed_count,
            "blocked": blocked_count,
            "clock_time": round(clock.now(), 2),
            "results": results
        }

    @app.post("/api/clock/advance")
    def advance_clock(payload: AdvanceClockPayload):
        try:
            clock.advance(payload.seconds)
            return {"status": "advanced", "clock_time": round(clock.now(), 2), "delta": payload.seconds}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/clock/set")
    def set_clock(payload: SetClockPayload):
        clock.set_time(payload.timestamp)
        return {"status": "set", "clock_time": round(clock.now(), 2)}

    @app.post("/api/config")
    def update_config(payload: ConfigPayload):
        if payload.limit <= 0 or payload.window_seconds <= 0:
            raise HTTPException(status_code=400, detail="Limit and window_seconds must be positive")
        config.limit = payload.limit
        config.window_seconds = payload.window_seconds
        limiter.config = config
        return {"status": "updated", "config": {"limit": config.limit, "window_seconds": config.window_seconds}}

    @app.post("/api/reset")
    def reset_state():
        store.clear()
        clock.set_time(1000.0)
        config.limit = 10
        config.window_seconds = 60.0
        limiter.config = config
        # Re-populate demo client
        gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now()))
        gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now() + 5.0))
        return {"status": "reset", "clock_time": round(clock.now(), 2)}

    def run_server(port: int = 8000):
        print(f"🚀 Starting CloudGate API Gateway (FastAPI) on http://0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError:
    # Zero-dependency Fallback: Standard Library http.server
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class FallbackHTTPHandler(BaseHTTPRequestHandler):
        def _set_cors(self, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

        def do_OPTIONS(self):
            self._set_cors(200)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/health":
                self._set_cors(200)
                self.wfile.write(json.dumps({"status": "healthy", "service": "CloudGate Rate Limiter Gateway"}).encode("utf-8"))
            elif path == "/api/state":
                self._set_cors(200)
                self.wfile.write(json.dumps(get_current_state()).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

        def do_POST(self):
            path = self.path.split("?")[0]
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

            if path == "/api/request":
                client_id = payload.get("client_id")
                endpoint = payload.get("endpoint", "/api/resource")
                try:
                    status_code, headers, body = gateway.handle_request(
                        ClientRequest(client_id, endpoint, clock.now())
                    )
                    self._set_cors(200)
                    self.wfile.write(json.dumps({
                        "status_code": status_code,
                        "headers": headers,
                        "body": body,
                        "clock_time": round(clock.now(), 2)
                    }).encode("utf-8"))
                except ValueError as e:
                    self._set_cors(400)
                    self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))

            elif path == "/api/burst":
                client_id = payload.get("client_id", "client-burst")
                count = int(payload.get("count", 5))
                endpoint = payload.get("endpoint", "/api/resource")
                results = []
                allowed_count = 0
                blocked_count = 0
                for _ in range(count):
                    status_code, headers, body = gateway.handle_request(
                        ClientRequest(client_id, endpoint, clock.now())
                    )
                    if status_code == 200:
                        allowed_count += 1
                    else:
                        blocked_count += 1
                    results.append({
                        "status_code": status_code,
                        "headers": headers,
                        "body": body
                    })
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "client_id": client_id,
                    "total_requested": count,
                    "allowed": allowed_count,
                    "blocked": blocked_count,
                    "clock_time": round(clock.now(), 2),
                    "results": results
                }).encode("utf-8"))

            elif path == "/api/clock/advance":
                seconds = float(payload.get("seconds", 10.0))
                try:
                    clock.advance(seconds)
                    self._set_cors(200)
                    self.wfile.write(json.dumps({
                        "status": "advanced",
                        "clock_time": round(clock.now(), 2),
                        "delta": seconds
                    }).encode("utf-8"))
                except ValueError as e:
                    self._set_cors(400)
                    self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))

            elif path == "/api/clock/set":
                ts = float(payload.get("timestamp", 1000.0))
                clock.set_time(ts)
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "status": "set",
                    "clock_time": round(clock.now(), 2)
                }).encode("utf-8"))

            elif path == "/api/config":
                lim = int(payload.get("limit", 10))
                win = float(payload.get("window_seconds", 60.0))
                config.limit = lim
                config.window_seconds = win
                limiter.config = config
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "status": "updated",
                    "config": {"limit": config.limit, "window_seconds": config.window_seconds}
                }).encode("utf-8"))

            elif path == "/api/reset":
                store.clear()
                clock.set_time(1000.0)
                config.limit = 10
                config.window_seconds = 60.0
                limiter.config = config
                gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now()))
                gateway.handle_request(ClientRequest("client-demo", "/api/v1/metrics", clock.now() + 5.0))
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "status": "reset",
                    "clock_time": round(clock.now(), 2)
                }).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

    def run_server(port: int = 8000):
        print(f"🚀 Starting CloudGate API Gateway (Standard Library HTTP Fallback) on http://0.0.0.0:{port}")
        server = HTTPServer(("0.0.0.0", port), FallbackHTTPHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)

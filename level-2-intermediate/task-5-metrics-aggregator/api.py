"""
api.py - CloudMetric Aggregator Backend Service
Provides REST API endpoints with FastAPI and built-in http.server fallback.
"""

import sys
import os
import json
import math
from typing import Optional, List, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from models import MetricDataPoint, TimeWindow, AggregatedBucket
from bucketer import WindowBucketer
from aggregator import MetricAggregator

PORT = 8000

# Global in-memory aggregator instance
aggregator = MetricAggregator(window_seconds=60)


def seed_demo_data():
    aggregator._data_points.clear()

    # Latency samples with quiet window [60, 120) and exact boundary point at 60.0
    latency_points = [
        # Window [0, 60)
        MetricDataPoint("api_latency_ms", 10.5, 45.0),
        MetricDataPoint("api_latency_ms", 22.1, 88.0),
        MetricDataPoint("api_latency_ms", 35.8, 32.0),
        MetricDataPoint("api_latency_ms", 48.0, 120.0),
        MetricDataPoint("api_latency_ms", 59.9, 65.0),

        # Exact boundary point: timestamp 60.0 belongs to [60, 120)
        MetricDataPoint("api_latency_ms", 60.0, 75.0),

        # Window [120, 180) - Window [60, 120) is mostly empty
        MetricDataPoint("api_latency_ms", 125.0, 110.0),
        MetricDataPoint("api_latency_ms", 140.2, 95.0),
        MetricDataPoint("api_latency_ms", 155.0, 210.0),
        MetricDataPoint("api_latency_ms", 172.4, 85.0),

        # Window [180, 240)
        MetricDataPoint("api_latency_ms", 185.0, 55.0),
        MetricDataPoint("api_latency_ms", 195.0, 60.0),
        MetricDataPoint("api_latency_ms", 215.0, 78.0),
        MetricDataPoint("api_latency_ms", 230.0, 145.0),

        # Window [240, 300)
        MetricDataPoint("api_latency_ms", 250.0, 50.0),
        MetricDataPoint("api_latency_ms", 270.0, 52.0),
        MetricDataPoint("api_latency_ms", 290.0, 48.0),
    ]

    cpu_points = [
        MetricDataPoint("cpu_utilization", 15.0, 25.4),
        MetricDataPoint("cpu_utilization", 45.0, 38.2),
        MetricDataPoint("cpu_utilization", 135.0, 72.1),
        MetricDataPoint("cpu_utilization", 195.0, 84.6),
        MetricDataPoint("cpu_utilization", 255.0, 41.0),
    ]

    aggregator.ingest_batch(latency_points + cpu_points)


seed_demo_data()


def serialize_bucket(b: AggregatedBucket) -> dict:
    return {
        "metric_name": b.metric_name,
        "start_time": b.window.start_time,
        "end_time": b.window.end_time,
        "count": b.count,
        "min": round(b.min_val, 2),
        "max": round(b.max_val, 2),
        "avg": round(b.avg_val, 2),
        "p95": round(b.p95_val, 2),
    }


def serialize_point(p: MetricDataPoint) -> dict:
    return {
        "metric_name": p.metric_name,
        "timestamp": p.timestamp,
        "value": p.value,
        "tags": p.tags,
    }


try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn

    app = FastAPI(title="CloudMetric Telemetry Aggregator API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class IngestPointRequest(BaseModel):
        metric_name: str
        timestamp: float
        value: float
        tags: Dict[str, str] = Field(default_factory=dict)

    class AggregateRequest(BaseModel):
        metric_name: str
        start_time: float = 0.0
        end_time: float = 300.0
        window_seconds: Optional[int] = 60
        fill_empty_windows: bool = True

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "cloudmetric-aggregator", "engine": "FastAPI"}

    @app.get("/api/state")
    def get_state():
        metrics = {m: len(pts) for m, pts in aggregator._data_points.items()}
        return {
            "metrics": metrics,
            "total_points": sum(len(pts) for pts in aggregator._data_points.values()),
        }

    @app.get("/api/points")
    def get_points(metric_name: str = Query("api_latency_ms")):
        pts = aggregator._data_points.get(metric_name, [])
        return {"metric_name": metric_name, "points": [serialize_point(p) for p in pts]}

    @app.post("/api/ingest")
    def ingest_endpoint(payload: IngestPointRequest):
        try:
            pt = MetricDataPoint(
                metric_name=payload.metric_name,
                timestamp=payload.timestamp,
                value=payload.value,
                tags=payload.tags,
            )
            aggregator.ingest(pt)
            return {"success": True, "point": serialize_point(pt)}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/aggregate")
    def aggregate_endpoint(payload: AggregateRequest):
        try:
            if payload.window_seconds:
                aggregator.window_seconds = payload.window_seconds
            buckets = aggregator.aggregate_metric(
                metric_name=payload.metric_name,
                start_time=payload.start_time,
                end_time=payload.end_time,
                fill_empty_windows=payload.fill_empty_windows,
            )
            return {
                "metric_name": payload.metric_name,
                "window_seconds": aggregator.window_seconds,
                "buckets": [serialize_bucket(b) for b in buckets],
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/reset")
    def reset_state():
        seed_demo_data()
        return {"success": True, "message": "Telemetry aggregator reset to default demo data"}

    def run_server():
        print(f"🚀 CloudMetric FastAPI server running on http://localhost:{PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)

except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs

    class MetricHandler(BaseHTTPRequestHandler):
        def _send_cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self):
            self.send_response(204)
            self._send_cors()
            self.end_headers()

        def _json(self, status: int, data: dict):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            params = parse_qs(parsed.query)

            if path == "/api/health":
                self._json(200, {"status": "ok", "app": "cloudmetric-aggregator", "engine": "Fallback-HTTP"})
            elif path == "/api/state":
                metrics = {m: len(pts) for m, pts in aggregator._data_points.items()}
                self._json(200, {
                    "metrics": metrics,
                    "total_points": sum(len(pts) for pts in aggregator._data_points.values()),
                })
            elif path == "/api/points":
                m_name = params.get("metric_name", ["api_latency_ms"])[0]
                pts = aggregator._data_points.get(m_name, [])
                self._json(200, {"metric_name": m_name, "points": [serialize_point(p) for p in pts]})
            else:
                self._json(404, {"detail": "Endpoint not found"})

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path

            length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(length) if length > 0 else b"{}"
            try:
                payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception:
                payload = {}

            if path == "/api/ingest":
                m_name = payload.get("metric_name", "")
                ts = float(payload.get("timestamp", 0.0))
                val = float(payload.get("value", 0.0))
                tags = payload.get("tags", {})
                try:
                    pt = MetricDataPoint(metric_name=m_name, timestamp=ts, value=val, tags=tags)
                    aggregator.ingest(pt)
                    self._json(200, {"success": True, "point": serialize_point(pt)})
                except ValueError as e:
                    self._json(400, {"detail": str(e)})
                except Exception as e:
                    self._json(500, {"detail": str(e)})

            elif path == "/api/aggregate":
                m_name = payload.get("metric_name", "api_latency_ms")
                start = float(payload.get("start_time", 0.0))
                end = float(payload.get("end_time", 300.0))
                win_sec = payload.get("window_seconds", 60)
                win_sec = int(win_sec) if win_sec is not None else None
                fill_empty = bool(payload.get("fill_empty_windows", True))

                try:
                    if win_sec:
                        aggregator.window_seconds = win_sec
                    buckets = aggregator.aggregate_metric(
                        metric_name=m_name,
                        start_time=start,
                        end_time=end,
                        fill_empty_windows=fill_empty,
                    )
                    self._json(200, {
                        "metric_name": m_name,
                        "window_seconds": aggregator.window_seconds,
                        "buckets": [serialize_bucket(b) for b in buckets],
                    })
                except ValueError as e:
                    self._json(400, {"detail": str(e)})
                except Exception as e:
                    self._json(500, {"detail": str(e)})

            elif path == "/api/reset":
                seed_demo_data()
                self._json(200, {"success": True, "message": "Telemetry aggregator reset to default demo data"})

            else:
                self._json(404, {"detail": "Endpoint not found"})

    def run_server():
        server = HTTPServer(("0.0.0.0", PORT), MetricHandler)
        print(f"🚀 CloudMetric Fallback HTTP server running on http://localhost:{PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()


if __name__ == "__main__":
    run_server()

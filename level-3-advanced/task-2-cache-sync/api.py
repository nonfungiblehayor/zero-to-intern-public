#!/usr/bin/env python3
"""
CacheSync - Write-Through Cache Manager REST API
Dual-mode server: Runs FastAPI if installed, falls back to Python stdlib http.server.
"""

import sys
import os
import json
from typing import Optional, List, Dict, Any

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models import CacheEntry, CacheStats
from clock import TestClock
from storage import InMemoryBackingStore
from cache_manager import WriteThroughCacheManager

# Initialize in-memory BackingStore & CacheManager with TestClock
clock = TestClock(initial_time=1000.0)
backing_store = InMemoryBackingStore()
manager = WriteThroughCacheManager(
    backing_store=backing_store,
    clock=clock,
    max_size=3  # Small size to showcase LRU eviction clearly
)

# Pre-populate demo entries
backing_store.write("config:system_version", "v3.4.1")
manager.put("session:user_42", {"user_id": 42, "role": "admin"}, ttl_seconds=300.0)
manager.put("profile:user_42", {"name": "Alex Vance", "theme": "dark"})


def get_current_state() -> Dict[str, Any]:
    now = clock.now()
    
    # Inspect cache entries
    cache_entries = {}
    for key, entry in manager._cache._entries.items():
        cache_entries[key] = {
            "value": entry.value,
            "created_at": round(entry.created_at, 2),
            "expires_at": round(entry.expires_at, 2) if entry.expires_at is not None else None,
            "is_expired": (entry.expires_at is not None and entry.expires_at <= now),
            "is_dirty": entry.is_dirty
        }

    # Inspect write buffer
    write_buffer = {}
    for key, entry in manager._write_buffer.items():
        write_buffer[key] = {
            "value": entry.value,
            "created_at": round(entry.created_at, 2),
            "expires_at": round(entry.expires_at, 2) if entry.expires_at is not None else None,
            "is_expired": (entry.expires_at is not None and entry.expires_at <= now),
            "is_dirty": entry.is_dirty
        }

    return {
        "clock_time": round(now, 2),
        "stats": {
            "hits": manager.stats.hits,
            "misses": manager.stats.misses,
            "evictions": manager.stats.evictions,
            "flushes": manager.stats.flushes
        },
        "max_size": manager._cache.max_size,
        "pending_write_count": manager.get_pending_write_count(),
        "cache_count": len(manager._cache._entries),
        "cache_entries": cache_entries,
        "write_buffer": write_buffer,
        "backing_store": dict(backing_store._data)
    }


# Try FastAPI first
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel

    app = FastAPI(title="CacheSync Write-Through Cache Manager API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class PutPayload(BaseModel):
        key: str
        value: Any
        ttl_seconds: Optional[float] = None

    class AdvanceClockPayload(BaseModel):
        seconds: float = 10.0

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "CacheSync Write-Through Cache Manager"}

    @app.get("/api/state")
    def state():
        return get_current_state()

    @app.get("/api/cache/{key}")
    def get_cache_key(key: str):
        try:
            val = manager.get(key)
            return {
                "key": key,
                "value": val,
                "found": val is not None,
                "clock_time": round(clock.now(), 2)
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/cache")
    def put_cache_key(payload: PutPayload):
        try:
            manager.put(payload.key, payload.value, payload.ttl_seconds)
            return {
                "status": "stored",
                "key": payload.key,
                "pending_writes": manager.get_pending_write_count(),
                "clock_time": round(clock.now(), 2)
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/flush")
    def flush_writes():
        count = manager.flush()
        return {
            "status": "flushed",
            "flushed_count": count,
            "pending_writes": manager.get_pending_write_count(),
            "clock_time": round(clock.now(), 2)
        }

    @app.post("/api/clock/advance")
    def advance_clock(payload: AdvanceClockPayload):
        try:
            clock.advance(payload.seconds)
            return {
                "status": "advanced",
                "clock_time": round(clock.now(), 2),
                "delta": payload.seconds
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/reset")
    def reset_state():
        global clock, backing_store, manager
        clock = TestClock(initial_time=1000.0)
        backing_store = InMemoryBackingStore()
        manager = WriteThroughCacheManager(
            backing_store=backing_store,
            clock=clock,
            max_size=3
        )
        backing_store.write("config:system_version", "v3.4.1")
        manager.put("session:user_42", {"user_id": 42, "role": "admin"}, ttl_seconds=300.0)
        manager.put("profile:user_42", {"name": "Alex Vance", "theme": "dark"})
        return {"status": "reset", "clock_time": round(clock.now(), 2)}

    def run_server(port: int = 8000):
        print(f"🚀 Starting CacheSync Manager (FastAPI) on http://0.0.0.0:{port}")
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
                self.wfile.write(json.dumps({"status": "healthy", "service": "CacheSync Write-Through Cache Manager"}).encode("utf-8"))
            elif path == "/api/state":
                self._set_cors(200)
                self.wfile.write(json.dumps(get_current_state()).encode("utf-8"))
            elif path.startswith("/api/cache/"):
                key = path[len("/api/cache/"):]
                try:
                    val = manager.get(key)
                    self._set_cors(200)
                    self.wfile.write(json.dumps({
                        "key": key,
                        "value": val,
                        "found": val is not None,
                        "clock_time": round(clock.now(), 2)
                    }).encode("utf-8"))
                except ValueError as e:
                    self._set_cors(400)
                    self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

        def do_POST(self):
            global clock, backing_store, manager
            path = self.path.split("?")[0]
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

            if path == "/api/cache":
                key = payload.get("key")
                value = payload.get("value")
                ttl = payload.get("ttl_seconds")
                try:
                    manager.put(key, value, ttl)
                    self._set_cors(200)
                    self.wfile.write(json.dumps({
                        "status": "stored",
                        "key": key,
                        "pending_writes": manager.get_pending_write_count(),
                        "clock_time": round(clock.now(), 2)
                    }).encode("utf-8"))
                except ValueError as e:
                    self._set_cors(400)
                    self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))

            elif path == "/api/flush":
                count = manager.flush()
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "status": "flushed",
                    "flushed_count": count,
                    "pending_writes": manager.get_pending_write_count(),
                    "clock_time": round(clock.now(), 2)
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

            elif path == "/api/reset":
                clock = TestClock(initial_time=1000.0)
                backing_store = InMemoryBackingStore()
                manager = WriteThroughCacheManager(
                    backing_store=backing_store,
                    clock=clock,
                    max_size=3
                )
                backing_store.write("config:system_version", "v3.4.1")
                manager.put("session:user_42", {"user_id": 42, "role": "admin"}, ttl_seconds=300.0)
                manager.put("profile:user_42", {"name": "Alex Vance", "theme": "dark"})
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "status": "reset",
                    "clock_time": round(clock.now(), 2)
                }).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

    def run_server(port: int = 8000):
        print(f"🚀 Starting CacheSync Manager (Standard Library HTTP Fallback) on http://0.0.0.0:{port}")
        server = HTTPServer(("0.0.0.0", port), FallbackHTTPHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)

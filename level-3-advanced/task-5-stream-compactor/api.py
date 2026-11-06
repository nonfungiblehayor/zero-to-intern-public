import os
import sys
import json
import time
import traceback
from typing import Dict, Any, List, Optional

# Ensure src is on sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from models import EventRecord, SegmentMetadata
from segment import LogSegment
from compactor import StreamCompactor
from stream_reader import PartitionStreamReader


class StreamService:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.reset_partition()

    def reset_partition(self):
        self.compactor = StreamCompactor(start_compacted_id=1000)
        self.segments: List[LogSegment] = []
        self.current_offset = 0

        # Create Segment 0
        seg0 = LogSegment(segment_id=0, max_records=10)
        seg0.append(EventRecord("user:alice", "Alice v1 (Active)", offset=self._next_offset(), timestamp_ms=1000))
        seg0.append(EventRecord("user:bob", "Bob v1 (Active)", offset=self._next_offset(), timestamp_ms=1010))
        seg0.append(EventRecord("config:theme", "dark", offset=self._next_offset(), timestamp_ms=1020))
        self.segments.append(seg0)

        # Create Segment 1
        seg1 = LogSegment(segment_id=1, max_records=10)
        seg1.append(EventRecord("user:alice", "Alice v2 (Promoted)", offset=self._next_offset(), timestamp_ms=1100))
        seg1.append(EventRecord("user:bob", None, offset=self._next_offset(), timestamp_ms=1110))  # Tombstone
        seg1.append(EventRecord("sensor:temp", "24.5C", offset=self._next_offset(), timestamp_ms=1120))
        self.segments.append(seg1)

        # Set Consumer Watermarks
        self.compactor.set_consumer_watermark("consumer:analytics", 5)
        self.compactor.set_consumer_watermark("consumer:indexer-lagging", 2)

        self.history.append({
            "action": "PARTITION_RESET",
            "segments_count": len(self.segments),
            "total_records": sum(len(s.records) for s in self.segments)
        })

    def _next_offset(self) -> int:
        off = self.current_offset
        self.current_offset += 1
        return off

    def get_state(self) -> Dict[str, Any]:
        reader = PartitionStreamReader(self.segments)
        materialized = reader.get_latest_state()

        segments_data = []
        for s in self.segments:
            recs_data = []
            for r in s.records:
                recs_data.append({
                    "key": r.key,
                    "value": r.value,
                    "offset": r.offset,
                    "timestamp_ms": r.timestamp_ms,
                    "is_tombstone": r.is_tombstone
                })

            segments_data.append({
                "segment_id": s.segment_id,
                "start_offset": s.start_offset,
                "end_offset": s.end_offset,
                "record_count": len(s.records),
                "is_compacted": s.segment_id >= 1000,
                "records": recs_data,
                "index": dict(s.index)
            })

        return {
            "safe_compaction_watermark": self.compactor.get_safe_compaction_watermark(),
            "consumer_watermarks": dict(self.compactor.consumer_watermarks),
            "segments": segments_data,
            "materialized_state": materialized,
            "total_records": sum(len(s.records) for s in self.segments),
            "current_offset": self.current_offset,
            "history": self.history[-30:]
        }

    def append_record(self, key: str, value: Optional[str], segment_id: Optional[int] = None) -> Dict[str, Any]:
        if not key:
            raise ValueError("Record key cannot be empty")

        # Choose target segment
        target_seg = None
        if segment_id is not None:
            for s in self.segments:
                if s.segment_id == segment_id:
                    target_seg = s
                    break

        if target_seg is None:
            if not self.segments or self.segments[-1].is_full():
                new_id = (max((s.segment_id for s in self.segments), default=-1) + 1)
                target_seg = LogSegment(segment_id=new_id, max_records=10)
                self.segments.append(target_seg)
            else:
                target_seg = self.segments[-1]

        offset = self._next_offset()
        now_ms = int(time.time() * 1000) % 1000000
        rec = EventRecord(key=key, value=value, offset=offset, timestamp_ms=now_ms)
        target_seg.append(rec)

        self.history.append({
            "action": "RECORD_APPENDED",
            "key": key,
            "is_tombstone": value is None,
            "offset": offset,
            "segment_id": target_seg.segment_id
        })

        return self.get_state()

    def set_watermark(self, consumer_id: str, offset: int) -> Dict[str, Any]:
        self.compactor.set_consumer_watermark(consumer_id, offset)
        self.history.append({
            "action": "WATERMARK_UPDATED",
            "consumer_id": consumer_id,
            "offset": offset,
            "safe_watermark": self.compactor.get_safe_compaction_watermark()
        })
        return self.get_state()

    def compact(self, segment_ids_to_compact: List[int], older_segment_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        to_compact = [s for s in self.segments if s.segment_id in segment_ids_to_compact]
        if not to_compact:
            raise ValueError("No matching segments found to compact")

        older_segs = None
        if older_segment_ids is not None:
            older_segs = [s for s in self.segments if s.segment_id in older_segment_ids]
        else:
            # By default, treat all segments with id < min(to_compact) as older
            min_target_id = min(s.segment_id for s in to_compact)
            older_segs = [s for s in self.segments if s.segment_id < min_target_id]

        compacted = self.compactor.compact_segments(to_compact, older_segments=older_segs)

        # Replace compacted segments in self.segments
        new_segments = []
        replaced = False
        for s in self.segments:
            if s.segment_id in segment_ids_to_compact:
                if not replaced:
                    new_segments.append(compacted)
                    replaced = True
            else:
                new_segments.append(s)

        if not replaced:
            new_segments.append(compacted)

        self.segments = new_segments

        self.history.append({
            "action": "SEGMENTS_COMPACTED",
            "compacted_id": compacted.segment_id,
            "input_segments": segment_ids_to_compact,
            "records_before": sum(len(s.records) for s in to_compact),
            "records_after": len(compacted.records)
        })

        return self.get_state()

    def lookup(self, key: str) -> Dict[str, Any]:
        reader = PartitionStreamReader(self.segments)
        try:
            rec = reader.get_record(key)
            if rec is None:
                return {"found": False, "key": key, "record": None}
            return {
                "found": True,
                "key": key,
                "record": {
                    "key": rec.key,
                    "value": rec.value,
                    "offset": rec.offset,
                    "timestamp_ms": rec.timestamp_ms,
                    "is_tombstone": rec.is_tombstone
                }
            }
        except IndexError as e:
            return {
                "found": False,
                "error": f"IndexError during lookup: {str(e)}",
                "corrupted": True
            }

    def reproduce(self, ticket_id: str) -> Dict[str, Any]:
        ticket = ticket_id.upper().strip()
        if not ticket.startswith("#"):
            ticket = f"#{ticket}"

        if "STREAM-901" in ticket:
            # Ghost Record Resurrection reproduction
            c = StreamCompactor()
            seg0 = LogSegment(segment_id=0)
            seg0.append(EventRecord("user1", "Alice", offset=0, timestamp_ms=100))
            seg0.append(EventRecord("user2", "Bob", offset=1, timestamp_ms=101))

            seg1 = LogSegment(segment_id=1)
            seg1.append(EventRecord("user1", None, offset=2, timestamp_ms=200))  # Tombstone

            compacted_seg1 = c.compact_segments([seg1], older_segments=[seg0])
            rec_user1 = compacted_seg1.get("user1")
            reader = PartitionStreamReader([seg0, compacted_seg1])
            state = reader.get_latest_state()

            resurrected = (state.get("user1") == "Alice")
            tombstone_kept = (rec_user1 is not None and rec_user1.is_tombstone)

            return {
                "ticket": "#STREAM-901",
                "description": "Ghost Record Scenario",
                "tombstone_retained_in_compacted": tombstone_kept,
                "materialized_state": state,
                "resurrected": resurrected,
                "verdict": ("Unexpected result observed." if resurrected else "Result matches expectations."),
                "state": self.get_state()
            }

        elif "STREAM-902" in ticket:
            # Watermark Regression reproduction
            c = StreamCompactor()
            c.set_consumer_watermark("consumer-fast", 500)
            c.set_consumer_watermark("consumer-lagging", 50)
            safe_watermark = c.get_safe_compaction_watermark()

            unexpected_result = (safe_watermark == 500)
            return {
                "ticket": "#STREAM-902",
                "description": "Watermark Scenario",
                "consumer_fast": 500,
                "consumer_lagging": 50,
                "safe_watermark_calculated": safe_watermark,
                "verdict": ("Unexpected result observed." if unexpected_result else "Result matches expectations."),
                "state": self.get_state()
            }

        elif "STREAM-903" in ticket:
            # Sparse index offset corruption reproduction
            c = StreamCompactor()
            seg = LogSegment(segment_id=5)
            seg.append(EventRecord("device:1", "active", offset=50, timestamp_ms=100))
            seg.append(EventRecord("device:2", "standby", offset=60, timestamp_ms=101))
            seg.append(EventRecord("device:3", "offline", offset=70, timestamp_ms=102))

            compacted = c.compact_segments([seg])
            try:
                r1 = compacted.get("device:1")
                val = r1.value if r1 else None
                return {
                    "ticket": "#STREAM-903",
                    "description": "Sparse Index Scenario",
                    "lookup_result": val,
                    "index_entry": compacted.index.get("device:1"),
                    "compacted_records_len": len(compacted.records),
                    "verdict": "Result matches expectations.",
                    "state": self.get_state()
                }
            except IndexError as e:
                return {
                    "ticket": "#STREAM-903",
                    "description": "Sparse Index Scenario",
                    "error": str(e),
                    "index_entry": compacted.index.get("device:1"),
                    "compacted_records_len": len(compacted.records),
                    "verdict": "Unexpected result observed.",
                    "state": self.get_state()
                }
        else:
            raise ValueError(f"Unknown ticket ID: {ticket_id}")


service = StreamService()


# ---------------------------------------------------------
# Framework selection: FastAPI with fallback to http.server
# ---------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="StreamCompactor Studio API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class AppendRequest(BaseModel):
        key: str
        value: Optional[str] = None
        segment_id: Optional[int] = None

    class WatermarkRequest(BaseModel):
        consumer_id: str
        offset: int

    class CompactRequest(BaseModel):
        segment_ids: List[int]
        older_segment_ids: Optional[List[int]] = None

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "StreamCompactor"}

    @app.get("/api/stream/state")
    def get_state():
        return service.get_state()

    @app.post("/api/stream/append")
    def append_record(req: AppendRequest):
        try:
            return service.append_record(req.key, req.value, req.segment_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/stream/watermark")
    def set_watermark(req: WatermarkRequest):
        try:
            return service.set_watermark(req.consumer_id, req.offset)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/stream/compact")
    def compact_segments(req: CompactRequest):
        try:
            return service.compact(req.segment_ids, req.older_segment_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/stream/lookup/{key}")
    def lookup_record(key: str):
        return service.lookup(key)

    @app.post("/api/stream/reset")
    def reset_stream():
        service.reset_partition()
        return service.get_state()

    @app.post("/api/reproduce/{ticket_id}")
    def reproduce(ticket_id: str):
        try:
            return service.reproduce(ticket_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def run_server(port: int = 8000):
        print(f"Starting StreamCompactor FastAPI server on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError:
    import http.server
    import urllib.parse

    class StandardHttpHandler(http.server.BaseHTTPRequestHandler):
        def _set_headers(self, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_OPTIONS(self):
            self._set_headers(200)

        def _read_json(self) -> Dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                return json.loads(raw_body)
            return {}

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            if path in ("/api/health", "/health"):
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "ok", "service": "StreamCompactor"}).encode("utf-8"))
            elif path == "/api/stream/state":
                self._set_headers(200)
                self.wfile.write(json.dumps(service.get_state()).encode("utf-8"))
            elif path.startswith("/api/stream/lookup/"):
                key = path.split("/api/stream/lookup/")[-1]
                key = urllib.parse.unquote(key)
                res = service.lookup(key)
                self._set_headers(200)
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": f"Not found: {self.path}"}).encode("utf-8"))

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            try:
                data = self._read_json()
                if path == "/api/stream/append":
                    key = data.get("key", "")
                    value = data.get("value")
                    segment_id = data.get("segment_id")
                    res = service.append_record(key, value, segment_id)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/stream/watermark":
                    consumer_id = data.get("consumer_id", "")
                    offset = int(data.get("offset", 0))
                    res = service.set_watermark(consumer_id, offset)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/stream/compact":
                    segment_ids = data.get("segment_ids", [])
                    older_ids = data.get("older_segment_ids")
                    res = service.compact(segment_ids, older_ids)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/stream/reset":
                    service.reset_partition()
                    self._set_headers(200)
                    self.wfile.write(json.dumps(service.get_state()).encode("utf-8"))
                elif path.startswith("/api/reproduce/"):
                    ticket_id = path.split("/api/reproduce/")[-1]
                    res = service.reproduce(ticket_id)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"Not found: {self.path}"}).encode("utf-8"))
            except ValueError as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e), "traceback": traceback.format_exc()}).encode("utf-8"))

    def run_server(port: int = 8000):
        print(f"Starting StreamCompactor Standard http.server on http://localhost:{port}")
        server = http.server.ThreadingHTTPServer(("0.0.0.0", port), StandardHttpHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port=port)

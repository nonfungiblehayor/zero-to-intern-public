"""
api.py - EventBridge Webhook Dispatcher Backend Service
Provides REST API endpoints with FastAPI and built-in http.server fallback.
"""

import sys
import os
import json
import time
from typing import Optional, List, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from models import WebhookEndpoint, WebhookEvent, DeliveryRecord, DeliveryAttempt, DeliveryStatus
from signer import WebhookSigner
from retry_policy import RetryPolicy
from dispatcher import WebhookDispatcher

PORT = 8000

# Global dispatcher instance
policy = RetryPolicy(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
dispatcher = WebhookDispatcher(retry_policy=policy)


def seed_demo_data():
    dispatcher._endpoints.clear()
    dispatcher._delivery_records.clear()

    ep1 = WebhookEndpoint(
        endpoint_id="ep_stripe_billing",
        url="https://api.partner.io/webhooks/billing",
        secret="whsec_test_secret_abc123",
        is_active=True,
    )
    ep2 = WebhookEndpoint(
        endpoint_id="ep_inventory_sync",
        url="https://inventory.partner.io/events",
        secret="whsec_inventory_key_999",
        is_active=True,
    )
    dispatcher.register_endpoint(ep1)
    dispatcher.register_endpoint(ep2)


seed_demo_data()


def serialize_endpoint(ep: WebhookEndpoint) -> dict:
    return {
        "endpoint_id": ep.endpoint_id,
        "url": ep.url,
        "secret": ep.secret,
        "is_active": ep.is_active,
    }


def serialize_attempt(a: DeliveryAttempt) -> dict:
    return {
        "attempt_number": a.attempt_number,
        "timestamp": a.timestamp,
        "status_code": a.status_code,
        "success": a.success,
        "error": a.error,
    }


def serialize_record(r: DeliveryRecord) -> dict:
    return {
        "event_id": r.event_id,
        "endpoint_id": r.endpoint_id,
        "status": r.status.value if hasattr(r.status, "value") else str(r.status),
        "next_retry_at": r.next_retry_at,
        "attempts": [serialize_attempt(a) for a in r.attempts],
    }


try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn

    app = FastAPI(title="EventBridge Webhook Dispatcher API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class CreateEndpointRequest(BaseModel):
        endpoint_id: str
        url: str
        secret: str

    class DispatchWebhookRequest(BaseModel):
        endpoint_id: str
        event_type: str
        payload: Dict[str, Any]
        mock_status_code: Optional[int] = 200
        mock_error: Optional[str] = None

    class VerifySignatureRequest(BaseModel):
        secret: str
        signature_header: str
        payload: Dict[str, Any]

    class SimulateBackoffRequest(BaseModel):
        max_attempts: int = 4
        initial_delay: float = 1.0
        backoff_factor: float = 2.0

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "eventbridge-webhook-dispatcher", "engine": "FastAPI"}

    @app.get("/api/state")
    def get_state():
        endpoints = [serialize_endpoint(e) for e in dispatcher._endpoints.values()]
        records = [serialize_record(r) for r in dispatcher._delivery_records.values()]
        return {"endpoints": endpoints, "deliveries": records}

    @app.post("/api/endpoints")
    def create_endpoint(payload: CreateEndpointRequest):
        ep = WebhookEndpoint(
            endpoint_id=payload.endpoint_id,
            url=payload.url,
            secret=payload.secret,
            is_active=True,
        )
        dispatcher.register_endpoint(ep)
        return {"success": True, "endpoint": serialize_endpoint(ep)}

    @app.post("/api/webhooks/dispatch")
    def dispatch_webhook(payload: DispatchWebhookRequest):
        event_id = f"evt_{int(time.time() * 1000)}"
        event = WebhookEvent(
            event_id=event_id,
            event_type=payload.event_type,
            payload=payload.payload,
            timestamp=time.time(),
        )

        def mock_client(url, headers, body_str):
            return payload.mock_status_code, payload.mock_error

        try:
            current_time = time.time()
            record = dispatcher.dispatch_event(
                event=event,
                endpoint_id=payload.endpoint_id,
                http_client=mock_client,
                current_time=current_time,
            )
            # Retrieve signature header generated
            ep = dispatcher.get_endpoint(payload.endpoint_id)
            sig_header = WebhookSigner.compute_signature(ep.secret, current_time, payload.payload)

            return {
                "success": True,
                "event_id": event_id,
                "signature_header": sig_header,
                "delivery": serialize_record(record),
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/webhooks/verify")
    def verify_signature(payload: VerifySignatureRequest):
        canonical_bytes = json.dumps(payload.payload, sort_keys=True, separators=(',', ':')).encode("utf-8")
        is_valid = WebhookSigner.verify_signature(payload.secret, payload.signature_header, canonical_bytes)
        return {"is_valid": is_valid}

    @app.post("/api/backoff/simulate")
    def simulate_backoff(payload: SimulateBackoffRequest):
        try:
            custom_policy = RetryPolicy(
                max_attempts=payload.max_attempts,
                initial_delay=payload.initial_delay,
                backoff_factor=payload.backoff_factor,
            )
            delays = [custom_policy.compute_next_delay(i) for i in range(1, payload.max_attempts + 1)]
            return {"delays": delays}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/reset")
    def reset_state():
        seed_demo_data()
        return {"success": True, "message": "Dispatcher state reset successfully"}

    def run_server():
        print(f"🚀 EventBridge FastAPI server running on http://localhost:{PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)

except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse

    class WebhookHandler(BaseHTTPRequestHandler):
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

            if path == "/api/health":
                self._json(200, {"status": "ok", "app": "eventbridge-webhook-dispatcher", "engine": "Fallback-HTTP"})
            elif path == "/api/state":
                endpoints = [serialize_endpoint(e) for e in dispatcher._endpoints.values()]
                records = [serialize_record(r) for r in dispatcher._delivery_records.values()]
                self._json(200, {"endpoints": endpoints, "deliveries": records})
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

            if path == "/api/endpoints":
                ep = WebhookEndpoint(
                    endpoint_id=payload.get("endpoint_id", ""),
                    url=payload.get("url", ""),
                    secret=payload.get("secret", ""),
                    is_active=True,
                )
                dispatcher.register_endpoint(ep)
                self._json(200, {"success": True, "endpoint": serialize_endpoint(ep)})

            elif path == "/api/webhooks/dispatch":
                endpoint_id = payload.get("endpoint_id", "")
                event_type = payload.get("event_type", "order.created")
                event_payload = payload.get("payload", {})
                mock_code = payload.get("mock_status_code", 200)
                mock_err = payload.get("mock_error", None)

                event_id = f"evt_{int(time.time() * 1000)}"
                event = WebhookEvent(
                    event_id=event_id,
                    event_type=event_type,
                    payload=event_payload,
                    timestamp=time.time(),
                )

                def mock_client(url, headers, body_str):
                    return mock_code, mock_err

                try:
                    cur_t = time.time()
                    record = dispatcher.dispatch_event(
                        event=event,
                        endpoint_id=endpoint_id,
                        http_client=mock_client,
                        current_time=cur_t,
                    )
                    ep = dispatcher.get_endpoint(endpoint_id)
                    sig_header = WebhookSigner.compute_signature(ep.secret, cur_t, event_payload) if ep else ""
                    self._json(200, {
                        "success": True,
                        "event_id": event_id,
                        "signature_header": sig_header,
                        "delivery": serialize_record(record),
                    })
                except ValueError as e:
                    self._json(400, {"detail": str(e)})
                except Exception as e:
                    self._json(500, {"detail": str(e)})

            elif path == "/api/webhooks/verify":
                secret = payload.get("secret", "")
                sig_header = payload.get("signature_header", "")
                raw_payload = payload.get("payload", {})
                canonical_bytes = json.dumps(raw_payload, sort_keys=True, separators=(',', ':')).encode("utf-8")
                is_valid = WebhookSigner.verify_signature(secret, sig_header, canonical_bytes)
                self._json(200, {"is_valid": is_valid})

            elif path == "/api/backoff/simulate":
                try:
                    max_attempts = int(payload.get("max_attempts", 4))
                    init_delay = float(payload.get("initial_delay", 1.0))
                    factor = float(payload.get("backoff_factor", 2.0))
                    p = RetryPolicy(max_attempts=max_attempts, initial_delay=init_delay, backoff_factor=factor)
                    delays = [p.compute_next_delay(i) for i in range(1, max_attempts + 1)]
                    self._json(200, {"delays": delays})
                except ValueError as e:
                    self._json(400, {"detail": str(e)})

            elif path == "/api/reset":
                seed_demo_data()
                self._json(200, {"success": True, "message": "Dispatcher state reset successfully"})

            else:
                self._json(404, {"detail": "Endpoint not found"})

    def run_server():
        server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
        print(f"🚀 EventBridge Fallback HTTP server running on http://localhost:{PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()


if __name__ == "__main__":
    run_server()

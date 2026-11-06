"""
api.py - AuthShield Session & Token Manager Backend Service
Provides REST API endpoints with FastAPI and built-in http.server fallback.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from session_store import SessionStore
from token_service import TokenService
from auth_middleware import AuthMiddleware
from models import TokenType

PORT = 8000

# Global in-memory security store and services
store = SessionStore()
token_service = TokenService(store)
auth_middleware = AuthMiddleware(token_service)


def seed_demo_data():
    store.clear()
    # Create an initial active session for alice
    now = datetime.utcnow()
    s1 = token_service.create_session("alice@authshield.io", current_time=now)
    token_service.issue_tokens(s1.session_id, current_time=now)

    # Create another session for bob
    s2 = token_service.create_session("bob@authshield.io", current_time=now)
    token_service.issue_tokens(s2.session_id, current_time=now)


seed_demo_data()


def serialize_session(s):
    return {
        "session_id": s.session_id,
        "user_id": s.user_id,
        "created_at": s.created_at.isoformat(),
        "expires_at": s.expires_at.isoformat(),
        "is_revoked": s.is_revoked,
    }


def serialize_token(t):
    return {
        "token_id": t.token_id,
        "session_id": t.session_id,
        "user_id": t.user_id,
        "token_type": t.token_type.value if hasattr(t.token_type, "value") else str(t.token_type),
        "created_at": t.created_at.isoformat(),
        "expires_at": t.expires_at.isoformat(),
        "is_used": t.is_used,
    }


try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional, List, Dict, Any
    import uvicorn

    app = FastAPI(title="AuthShield Session & Token API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class CreateSessionRequest(BaseModel):
        user_id: str

    class RefreshTokenRequest(BaseModel):
        refresh_token_id: str

    class ValidateTokenRequest(BaseModel):
        token_id: str

    class RevokeUserRequest(BaseModel):
        user_id: str

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "authshield-session-manager", "engine": "FastAPI"}

    @app.get("/api/state")
    def get_state():
        sessions = [serialize_session(s) for s in store._sessions.values()]
        tokens = [serialize_token(t) for t in store._tokens.values()]
        return {"sessions": sessions, "tokens": tokens}

    @app.post("/api/sessions")
    def create_session_endpoint(payload: CreateSessionRequest):
        try:
            now = datetime.utcnow()
            session = token_service.create_session(payload.user_id, current_time=now)
            acc, ref = token_service.issue_tokens(session.session_id, current_time=now)
            return {
                "success": True,
                "session": serialize_session(session),
                "access_token": serialize_token(acc),
                "refresh_token": serialize_token(ref),
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/sessions/{session_id}/revoke")
    def revoke_session_endpoint(session_id: str):
        revoked = store.revoke_session(session_id)
        if not revoked:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "session_id": session_id, "is_revoked": True}

    @app.post("/api/sessions/revoke-all")
    def revoke_user_sessions_endpoint(payload: RevokeUserRequest):
        count = store.revoke_user_sessions(payload.user_id)
        return {"success": True, "user_id": payload.user_id, "revoked_count": count}

    @app.post("/api/tokens/refresh")
    def refresh_token_endpoint(payload: RefreshTokenRequest):
        try:
            now = datetime.utcnow()
            acc, ref = token_service.refresh_token(payload.refresh_token_id, current_time=now)
            return {
                "success": True,
                "access_token": serialize_token(acc),
                "refresh_token": serialize_token(ref),
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/tokens/validate")
    def validate_token_endpoint(payload: ValidateTokenRequest):
        now = datetime.utcnow()
        result = token_service.validate_access_token(payload.token_id, current_time=now)
        return {
            "is_valid": result.is_valid,
            "user_id": result.user_id,
            "session_id": result.session_id,
            "error_code": result.error_code,
            "error_message": result.error_message,
        }

    @app.get("/api/protected")
    def protected_endpoint(request: Request, response: Response):
        headers = dict(request.headers)
        status, resp_headers, user_or_err = auth_middleware.authenticate_request(headers)
        for k, v in resp_headers.items():
            response.headers[k] = v
        if status != 200:
            raise HTTPException(status_code=status, detail=user_or_err)
        return {
            "authenticated": True,
            "user_id": user_or_err,
            "message": "Vault clearance granted. Confidential security payload accessed.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.post("/api/reset")
    def reset_state():
        seed_demo_data()
        return {"success": True, "message": "Demo data reset successfully"}

    def run_server():
        print(f"🚀 AuthShield FastAPI server running on http://localhost:{PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)

except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse

    class AuthShieldHandler(BaseHTTPRequestHandler):
        def _send_cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

        def do_OPTIONS(self):
            self.send_response(204)
            self._send_cors()
            self.end_headers()

        def _json(self, status: int, data: dict, extra_headers: Optional[dict] = None):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/api/health":
                self._json(200, {"status": "ok", "app": "authshield-session-manager", "engine": "Fallback-HTTP"})
            elif path == "/api/state":
                sessions = [serialize_session(s) for s in store._sessions.values()]
                tokens = [serialize_token(t) for t in store._tokens.values()]
                self._json(200, {"sessions": sessions, "tokens": tokens})
            elif path == "/api/protected":
                headers = dict(self.headers)
                status, resp_headers, user_or_err = auth_middleware.authenticate_request(headers)
                if status != 200:
                    self._json(status, {"detail": user_or_err}, resp_headers)
                else:
                    self._json(200, {
                        "authenticated": True,
                        "user_id": user_or_err,
                        "message": "Vault clearance granted. Confidential security payload accessed.",
                        "timestamp": datetime.utcnow().isoformat(),
                    }, resp_headers)
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

            if path == "/api/sessions":
                user_id = payload.get("user_id", "")
                try:
                    now = datetime.utcnow()
                    session = token_service.create_session(user_id, current_time=now)
                    acc, ref = token_service.issue_tokens(session.session_id, current_time=now)
                    self._json(200, {
                        "success": True,
                        "session": serialize_session(session),
                        "access_token": serialize_token(acc),
                        "refresh_token": serialize_token(ref),
                    })
                except ValueError as e:
                    self._json(400, {"detail": str(e)})
                except Exception as e:
                    self._json(500, {"detail": str(e)})

            elif path.startswith("/api/sessions/") and path.endswith("/revoke"):
                session_id = path.split("/")[3]
                revoked = store.revoke_session(session_id)
                if not revoked:
                    self._json(404, {"detail": "Session not found"})
                else:
                    self._json(200, {"success": True, "session_id": session_id, "is_revoked": True})

            elif path == "/api/sessions/revoke-all":
                user_id = payload.get("user_id", "")
                count = store.revoke_user_sessions(user_id)
                self._json(200, {"success": True, "user_id": user_id, "revoked_count": count})

            elif path == "/api/tokens/refresh":
                ref_id = payload.get("refresh_token_id", "")
                try:
                    now = datetime.utcnow()
                    acc, ref = token_service.refresh_token(ref_id, current_time=now)
                    self._json(200, {
                        "success": True,
                        "access_token": serialize_token(acc),
                        "refresh_token": serialize_token(ref),
                    })
                except ValueError as e:
                    self._json(400, {"detail": str(e)})
                except Exception as e:
                    self._json(500, {"detail": str(e)})

            elif path == "/api/tokens/validate":
                token_id = payload.get("token_id", "")
                now = datetime.utcnow()
                result = token_service.validate_access_token(token_id, current_time=now)
                self._json(200, {
                    "is_valid": result.is_valid,
                    "user_id": result.user_id,
                    "session_id": result.session_id,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                })

            elif path == "/api/reset":
                seed_demo_data()
                self._json(200, {"success": True, "message": "Demo data reset successfully"})

            else:
                self._json(404, {"detail": "Endpoint not found"})

    def run_server():
        server = HTTPServer(("0.0.0.0", PORT), AuthShieldHandler)
        print(f"🚀 AuthShield Fallback HTTP server running on http://localhost:{PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()


if __name__ == "__main__":
    run_server()

"""
EventBridge Webhook HMAC-SHA256 Payload Signer.
"""
import hmac
import hashlib
import json
from typing import Dict, Any


class WebhookSigner:
    @staticmethod
    def compute_signature(secret: str, timestamp: float, payload: Dict[str, Any]) -> str:
        """
        Generates an HMAC-SHA256 hex signature formatted as:
        t=<timestamp>,v1=<hex_signature>
        Signed payload format: "<timestamp>.<canonical_json_body>"
        """
        # DEFECT (Ticket #HOOK-401): Using str(payload) produces Python dict format
        # with single quotes (e.g. "{'foo': 'bar'}") rather than valid canonical JSON.
        # This causes HMAC verification to fail on standard HTTP consumer receivers.
        raw_body = str(payload)
        signed_payload = f"{int(timestamp)}.{raw_body}".encode("utf-8")
        
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        return f"t={int(timestamp)},v1={signature}"

    @staticmethod
    def verify_signature(secret: str, signature_header: str, canonical_json_bytes: bytes) -> bool:
        """
        Verifies that the provided signature header matches the canonical JSON bytes.
        """
        parts = dict(item.split("=", 1) for item in signature_header.split(","))
        timestamp_str = parts.get("t")
        expected_sig = parts.get("v1")

        if not timestamp_str or not expected_sig:
            return False

        signed_payload = f"{timestamp_str}.".encode("utf-8") + canonical_json_bytes
        computed = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, computed)

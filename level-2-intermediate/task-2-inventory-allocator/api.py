"""
api.py - ShipStream Inventory Allocator Backend Service
Provides REST endpoints for warehouse inventory inspection and order allocation.
"""

import sys
import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from warehouse import Warehouse
from models import OrderLine
from allocation_service import AllocationService
from exceptions import AllocationError

PORT = 8000

# Global in-memory warehouse state
def create_initial_warehouses():
    return [
        Warehouse(warehouse_id="WH-EAST", inventory={"SKU-LAPTOP": 10, "SKU-MOUSE": 5}),
        Warehouse(warehouse_id="WH-WEST", inventory={"SKU-LAPTOP": 5, "SKU-KEYBOARD": 8}),
    ]

warehouses = create_initial_warehouses()
service = AllocationService(warehouses)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Dict, Any
    import uvicorn

    app = FastAPI(title="ShipStream Inventory Allocation Service", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class OrderLineItem(BaseModel):
        sku: str
        quantity: int

    class AllocationRequest(BaseModel):
        order_id: str
        lines: List[OrderLineItem]

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "ShipStream Inventory Allocator", "engine": "FastAPI"}

    @app.get("/api/warehouses")
    def get_warehouses():
        return [
            {
                "warehouse_id": wh.warehouse_id,
                "inventory": wh.inventory,
                "reservations": wh.reservations,
                "available": {sku: wh.get_available_stock(sku) for sku in wh.inventory}
            }
            for wh in warehouses
        ]

    @app.post("/api/inventory/allocate")
    def allocate(req: AllocationRequest):
        try:
            order_lines = [OrderLine(sku=l.sku, quantity=l.quantity) for l in req.lines]
            result = service.allocate_order(req.order_id, order_lines)
            return {
                "success": True,
                "order_id": result.order_id,
                "reservations": [
                    {"warehouse_id": r.warehouse_id, "sku": r.sku, "quantity": r.quantity}
                    for r in result.reservations
                ]
            }
        except AllocationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

    @app.post("/api/inventory/reset")
    def reset_inventory():
        global warehouses, service
        warehouses = create_initial_warehouses()
        service = AllocationService(warehouses)
        return {"status": "reset", "message": "Warehouse inventory restored to initial values."}

    def run_server():
        print(f"🚀 ShipStream Allocation API starting on http://localhost:{PORT}")
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
                self.wfile.write(json.dumps({"status": "ok", "service": "ShipStream Inventory Allocator", "engine": "Builtin-HTTPServer"}).encode())
            elif self.path == "/api/warehouses":
                data = [
                    {
                        "warehouse_id": wh.warehouse_id,
                        "inventory": wh.inventory,
                        "reservations": wh.reservations,
                        "available": {sku: wh.get_available_stock(sku) for sku in wh.inventory}
                    }
                    for wh in warehouses
                ]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            global warehouses, service
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

            if self.path == "/api/inventory/reset":
                warehouses = create_initial_warehouses()
                service = AllocationService(warehouses)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "reset"}).encode())
            elif self.path == "/api/inventory/allocate":
                try:
                    payload = json.loads(body)
                    order_lines = [OrderLine(sku=l["sku"], quantity=l["quantity"]) for l in payload.get("lines", [])]
                    result = service.allocate_order(payload.get("order_id"), order_lines)
                    response_data = {
                        "success": True,
                        "order_id": result.order_id,
                        "reservations": [
                            {"warehouse_id": r.warehouse_id, "sku": r.sku, "quantity": r.quantity}
                            for r in result.reservations
                        ]
                    }
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                except AllocationError as e:
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
                    self.wfile.write(json.dumps({"detail": f"Internal Error: {str(e)}"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    def run_server():
        server = HTTPServer(("0.0.0.0", PORT), FallbackRequestHandler)
        print(f"🚀 ShipStream Allocation API starting on http://localhost:{PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()

import os
import sys
import json
import traceback
from typing import Dict, Any, List, Optional

# Ensure src is on sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from clock import SimulatedClock
from network import SimulatedNetwork
from node import ConsensusNode
from lease_manager import ClusterLeaseManager
from models import LeaseGrant


class ClusterService:
    def __init__(self, node_ids: Optional[List[str]] = None, rtt_latency_ms: int = 50, start_ms: int = 1000):
        self.start_ms = start_ms
        self.default_nodes = node_ids or ["N1", "N2", "N3", "N4", "N5"]
        self.rtt_latency_ms = rtt_latency_ms
        self.history: List[Dict[str, Any]] = []
        self._init_cluster()

    def _init_cluster(self):
        self.clock = SimulatedClock(start_ms=self.start_ms)
        self.network = SimulatedNetwork()
        self.manager = ClusterLeaseManager(self.clock, self.network, rtt_latency_ms=self.rtt_latency_ms)
        for node_id in self.default_nodes:
            self.manager.add_node(ConsensusNode(node_id, self.clock))
        self.history.append({
            "action": "CLUSTER_INIT",
            "clock_ms": self.clock.now_ms(),
            "nodes": list(self.default_nodes),
            "quorum": self.manager.get_quorum_size(),
            "rtt_ms": self.rtt_latency_ms
        })

    def get_state(self) -> Dict[str, Any]:
        now = self.clock.now_ms()
        nodes_state = []
        for node_id, node in self.manager.nodes.items():
            leases_repr = {}
            for res, grant in node.active_leases.items():
                leases_repr[res] = {
                    "leader_id": grant.leader_id,
                    "ballot": grant.ballot,
                    "granted_at_ms": grant.granted_at_ms,
                    "duration_ms": grant.duration_ms,
                    "expires_at_ms": grant.expires_at_ms,
                    "is_valid": now < grant.expires_at_ms
                }

            nodes_state.append({
                "node_id": node_id,
                "is_dropped": node_id in self.network.dropped_nodes,
                "local_ballot": self.manager.local_ballots.get(node_id, 0),
                "highest_promised_ballot": dict(node.highest_promised_ballot),
                "active_leases": leases_repr
            })

        cluster_leases_repr = {}
        for res, grant in self.manager.active_leases.items():
            cluster_leases_repr[res] = {
                "resource": res,
                "leader_id": grant.leader_id,
                "ballot": grant.ballot,
                "granted_at_ms": grant.granted_at_ms,
                "duration_ms": grant.duration_ms,
                "expires_at_ms": grant.expires_at_ms,
                "is_valid": self.manager.is_lease_valid(res, grant.leader_id)
            }

        # Build connectivity matrix
        node_ids = list(self.manager.nodes.keys())
        connectivity = {}
        for src in node_ids:
            connectivity[src] = {}
            for dst in node_ids:
                connectivity[src][dst] = self.network.can_communicate(src, dst)

        # Build partition list
        partitions = []
        for part in self.network.partitions:
            groups = list(part)
            if len(groups) == 2:
                partitions.append({
                    "group_a": sorted(list(groups[0])),
                    "group_b": sorted(list(groups[1]))
                })

        return {
            "clock_ms": now,
            "rtt_latency_ms": self.manager.rtt_latency_ms,
            "quorum_size": self.manager.get_quorum_size(),
            "total_nodes": len(self.manager.nodes),
            "nodes": nodes_state,
            "network": {
                "partitions": partitions,
                "dropped_nodes": sorted(list(self.network.dropped_nodes)),
                "connectivity": connectivity
            },
            "cluster_leases": cluster_leases_repr,
            "history": self.history[-30:]
        }

    def acquire_lease(self, candidate_id: str, resource: str, duration_ms: int = 1000) -> Dict[str, Any]:
        before_clock = self.clock.now_ms()
        quorum_req = self.manager.get_quorum_size()
        grant = self.manager.acquire_lease(candidate_id, resource, duration_ms)
        after_clock = self.clock.now_ms()

        success = grant is not None
        grant_dict = None
        if grant:
            grant_dict = {
                "resource": grant.resource,
                "leader_id": grant.leader_id,
                "ballot": grant.ballot,
                "granted_at_ms": grant.granted_at_ms,
                "duration_ms": grant.duration_ms,
                "expires_at_ms": grant.expires_at_ms,
                "is_valid": self.manager.is_lease_valid(grant.resource, grant.leader_id)
            }

        msg = (f"Candidate {candidate_id} acquired lease on '{resource}' (ballot {grant.ballot})"
               if success else
               f"Candidate {candidate_id} failed to acquire lease on '{resource}' (quorum: {quorum_req})")

        self.history.append({
            "action": "ACQUIRE_LEASE",
            "candidate_id": candidate_id,
            "resource": resource,
            "duration_ms": duration_ms,
            "success": success,
            "ballot": grant.ballot if grant else self.manager.local_ballots.get(candidate_id, 0),
            "clock_before": before_clock,
            "clock_after": after_clock,
            "message": msg
        })

        return {
            "success": success,
            "grant": grant_dict,
            "candidate_id": candidate_id,
            "resource": resource,
            "ballot": self.manager.local_ballots.get(candidate_id, 0),
            "quorum_required": quorum_req,
            "clock_ms": after_clock,
            "message": msg
        }

    def create_partition(self, group_a: List[str], group_b: List[str]) -> Dict[str, Any]:
        self.network.partition(set(group_a), set(group_b))
        self.history.append({
            "action": "PARTITION_CREATED",
            "clock_ms": self.clock.now_ms(),
            "group_a": sorted(group_a),
            "group_b": sorted(group_b)
        })
        return self.get_state()

    def heal_network(self) -> Dict[str, Any]:
        self.network.heal()
        self.history.append({
            "action": "NETWORK_HEALED",
            "clock_ms": self.clock.now_ms()
        })
        return self.get_state()

    def drop_node(self, node_id: str) -> Dict[str, Any]:
        self.network.drop_node(node_id)
        self.history.append({
            "action": "NODE_DROPPED",
            "node_id": node_id,
            "clock_ms": self.clock.now_ms()
        })
        return self.get_state()

    def recover_node(self, node_id: str) -> Dict[str, Any]:
        self.network.recover_node(node_id)
        self.history.append({
            "action": "NODE_RECOVERED",
            "node_id": node_id,
            "clock_ms": self.clock.now_ms()
        })
        return self.get_state()

    def advance_clock(self, delta_ms: int) -> Dict[str, Any]:
        self.clock.advance_ms(delta_ms)
        self.history.append({
            "action": "CLOCK_ADVANCED",
            "delta_ms": delta_ms,
            "new_clock_ms": self.clock.now_ms()
        })
        return self.get_state()

    def reset_cluster(self, node_ids: Optional[List[str]] = None, rtt_ms: int = 50, start_ms: int = 1000) -> Dict[str, Any]:
        self.default_nodes = node_ids or ["N1", "N2", "N3", "N4", "N5"]
        self.rtt_latency_ms = rtt_ms
        self.start_ms = start_ms
        self._init_cluster()
        return self.get_state()

    def reproduce(self, ticket_id: str) -> Dict[str, Any]:
        ticket = ticket_id.upper().strip()
        if not ticket.startswith("#"):
            ticket = f"#{ticket}"

        if "LEASE-801" in ticket:
            # 5-node cluster split brain reproduction
            self.reset_cluster(node_ids=["N1", "N2", "N3", "N4", "N5"], rtt_ms=50, start_ms=1000)
            self.create_partition(["N1", "N2"], ["N3", "N4", "N5"])
            res1 = self.acquire_lease("N1", "resource:catalog", duration_ms=1000)
            res2 = self.acquire_lease("N3", "resource:catalog", duration_ms=1000)

            has_split_brain = (res1["success"] and res2["success"])
            return {
                "ticket": "#LEASE-801",
                "description": "5-Node Partition Scenario",
                "quorum_calculated": self.manager.get_quorum_size(),
                "partition_minority_result": res1,
                "partition_majority_result": res2,
                "split_brain_detected": has_split_brain,
                "verdict": ("Unexpected result observed."
                            if has_split_brain else
                            "Result matches expectations."),
                "state": self.get_state()
            }

        elif "LEASE-802" in ticket:
            # Rejection livelock reproduction
            self.reset_cluster(node_ids=["N1", "N2", "N3"], rtt_ms=50, start_ms=1000)
            self.manager.nodes["N2"].highest_promised_ballot["resource:queue"] = 50
            self.manager.nodes["N3"].highest_promised_ballot["resource:queue"] = 50

            try1 = self.acquire_lease("N1", "resource:queue", duration_ms=1000)
            try2 = self.acquire_lease("N1", "resource:queue", duration_ms=1000)

            adopted = (self.manager.local_ballots.get("N1", 0) > 50)
            clean = adopted and (try2["grant"] is not None and try2["grant"]["ballot"] > 50)
            return {
                "ticket": "#LEASE-802",
                "description": "Election Rejection Scenario",
                "first_attempt": try1,
                "second_attempt": try2,
                "candidate_final_ballot": self.manager.local_ballots.get("N1", 0),
                "adopted_higher_ballot": adopted,
                "verdict": ("Result matches expectations." if clean else "Unexpected result observed."),
                "state": self.get_state()
            }

        elif "LEASE-803" in ticket:
            # Lease expiry RTT skew reproduction
            self.reset_cluster(node_ids=["N1", "N2", "N3"], rtt_ms=200, start_ms=1000)
            grant_res = self.acquire_lease("N1", "resource:lock", duration_ms=1000)
            
            # Clock before advance is 1200ms (1000 start + 200 RTT).
            # Advance clock by 850ms to 2050ms.
            self.advance_clock(850)
            validity_now = self.manager.is_lease_valid("resource:lock", "N1")

            return {
                "ticket": "#LEASE-803",
                "description": "Lease Expiry Scenario",
                "grant_result": grant_res,
                "clock_ms": self.clock.now_ms(),
                "leader_lease_valid": validity_now,
                "verdict": ("Unexpected result observed." if validity_now else "Result matches expectations."),
                "state": self.get_state()
            }

        else:
            raise ValueError(f"Unknown ticket ID: {ticket_id}")


service = ClusterService()


# ---------------------------------------------------------
# Framework selection: FastAPI with fallback to http.server
# ---------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="ConsensusLease Studio API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class AcquireRequest(BaseModel):
        candidate_id: str
        resource: str
        duration_ms: int = 1000

    class PartitionRequest(BaseModel):
        group_a: List[str]
        group_b: List[str]

    class NodeRequest(BaseModel):
        node_id: str

    class ClockRequest(BaseModel):
        delta_ms: int

    class ResetRequest(BaseModel):
        nodes: Optional[List[str]] = None
        rtt_latency_ms: int = 50
        start_ms: int = 1000

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "ConsensusLease"}

    @app.get("/api/cluster/state")
    def get_state():
        return service.get_state()

    @app.post("/api/lease/acquire")
    def acquire_lease(req: AcquireRequest):
        try:
            return service.acquire_lease(req.candidate_id, req.resource, req.duration_ms)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/network/partition")
    def partition_network(req: PartitionRequest):
        return service.create_partition(req.group_a, req.group_b)

    @app.post("/api/network/heal")
    def heal_network():
        return service.heal_network()

    @app.post("/api/network/drop")
    def drop_node(req: NodeRequest):
        return service.drop_node(req.node_id)

    @app.post("/api/network/recover")
    def recover_node(req: NodeRequest):
        return service.recover_node(req.node_id)

    @app.post("/api/clock/advance")
    def advance_clock(req: ClockRequest):
        return service.advance_clock(req.delta_ms)

    @app.post("/api/cluster/reset")
    def reset_cluster(req: ResetRequest):
        return service.reset_cluster(req.nodes, req.rtt_latency_ms, req.start_ms)

    @app.post("/api/reproduce/{ticket_id}")
    def reproduce(ticket_id: str):
        try:
            return service.reproduce(ticket_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def run_server(port: int = 8000):
        print(f"Starting ConsensusLease FastAPI server on http://localhost:{port}")
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
                self.wfile.write(json.dumps({"status": "ok", "service": "ConsensusLease"}).encode("utf-8"))
            elif path == "/api/cluster/state":
                self._set_headers(200)
                self.wfile.write(json.dumps(service.get_state()).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": f"Not found: {self.path}"}).encode("utf-8"))

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            try:
                data = self._read_json()
                if path == "/api/lease/acquire":
                    candidate_id = data.get("candidate_id", "N1")
                    resource = data.get("resource", "resource:default")
                    duration_ms = int(data.get("duration_ms", 1000))
                    res = service.acquire_lease(candidate_id, resource, duration_ms)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/network/partition":
                    group_a = data.get("group_a", [])
                    group_b = data.get("group_b", [])
                    res = service.create_partition(group_a, group_b)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/network/heal":
                    res = service.heal_network()
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/network/drop":
                    node_id = data.get("node_id", "")
                    res = service.drop_node(node_id)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/network/recover":
                    node_id = data.get("node_id", "")
                    res = service.recover_node(node_id)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/clock/advance":
                    delta_ms = int(data.get("delta_ms", 100))
                    res = service.advance_clock(delta_ms)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                elif path == "/api/cluster/reset":
                    nodes = data.get("nodes", ["N1", "N2", "N3", "N4", "N5"])
                    rtt_ms = int(data.get("rtt_latency_ms", 50))
                    start_ms = int(data.get("start_ms", 1000))
                    res = service.reset_cluster(nodes, rtt_ms, start_ms)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(res).encode("utf-8"))
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
        print(f"Starting ConsensusLease Standard http.server on http://localhost:{port}")
        server = http.server.ThreadingHTTPServer(("0.0.0.0", port), StandardHttpHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port=port)

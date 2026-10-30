#!/usr/bin/env python3
"""
TaskGraph Workflow Engine - DAG Runner & Visualizer REST API
Dual-mode server: Runs FastAPI if installed, falls back to Python stdlib http.server.
"""

import sys
import os
import json
from typing import Optional, List, Dict, Any, Set

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models import Task, TaskStatus, WorkflowResult
from graph import WorkflowGraph
from executor import WorkflowExecutor

# In-memory workflow definition store
task_definitions: Dict[str, Dict[str, Any]] = {}
execution_log: List[Dict[str, Any]] = []


def load_template(template_name: str):
    global task_definitions, execution_log
    task_definitions.clear()
    execution_log.clear()

    if template_name == "diamond":
        task_definitions["A"] = {"dependencies": [], "should_fail": False, "fail_message": ""}
        task_definitions["B"] = {"dependencies": ["A"], "should_fail": False, "fail_message": ""}
        task_definitions["C"] = {"dependencies": ["A"], "should_fail": False, "fail_message": ""}
        task_definitions["D"] = {"dependencies": ["B", "C"], "should_fail": False, "fail_message": ""}

    elif template_name == "cascade_fail":
        task_definitions["extract"] = {"dependencies": [], "should_fail": True, "fail_message": "Postgres connection reset by peer"}
        task_definitions["transform"] = {"dependencies": ["extract"], "should_fail": False, "fail_message": ""}
        task_definitions["load"] = {"dependencies": ["transform"], "should_fail": False, "fail_message": ""}

    elif template_name == "fan_in":
        task_definitions["A"] = {"dependencies": [], "should_fail": False, "fail_message": ""}
        task_definitions["X"] = {"dependencies": [], "should_fail": False, "fail_message": ""}
        task_definitions["B"] = {"dependencies": ["X"], "should_fail": False, "fail_message": ""}
        task_definitions["C"] = {"dependencies": ["A", "B"], "should_fail": False, "fail_message": ""}

    elif template_name == "cycle":
        task_definitions["solo"] = {"dependencies": [], "should_fail": False, "fail_message": ""}
        task_definitions["X"] = {"dependencies": ["Y"], "should_fail": False, "fail_message": ""}
        task_definitions["Y"] = {"dependencies": ["X"], "should_fail": False, "fail_message": ""}

    else:
        # Default workflow: ETL Pipeline
        task_definitions["ingest"] = {"dependencies": [], "should_fail": False, "fail_message": ""}
        task_definitions["clean"] = {"dependencies": ["ingest"], "should_fail": False, "fail_message": ""}
        task_definitions["aggregate"] = {"dependencies": ["clean"], "should_fail": False, "fail_message": ""}
        task_definitions["publish"] = {"dependencies": ["aggregate"], "should_fail": False, "fail_message": ""}


# Initial default
load_template("default")


def build_and_run_graph() -> Dict[str, Any]:
    global execution_log
    execution_log = []

    graph = WorkflowGraph()
    has_cycle = False

    for tid, tinfo in task_definitions.items():
        should_fail = tinfo.get("should_fail", False)
        fail_msg = tinfo.get("fail_message", "Deliberate failure")
        deps = set(tinfo.get("dependencies", []))

        def make_task_fn(task_name=tid, fails=should_fail, msg=fail_msg):
            def fn():
                execution_log.append({"task_id": task_name, "event": "RUNNING"})
                if fails:
                    execution_log.append({"task_id": task_name, "event": "FAILED", "error": msg})
                    raise RuntimeError(msg)
                execution_log.append({"task_id": task_name, "event": "COMPLETED"})
                return f"OK_{task_name}"
            return fn

        graph.add_task(Task(tid, make_task_fn(), dependencies=deps))

    has_cycle = graph.detect_cycles()
    if has_cycle:
        return {
            "is_successful": False,
            "has_cycle": True,
            "error": "Cyclic dependencies detected in graph! Workflow aborted.",
            "completed_tasks": [],
            "failed_tasks": [],
            "skipped_tasks": [],
            "task_results": {},
            "tasks": get_tasks_summary(graph)
        }

    executor = WorkflowExecutor(graph)
    try:
        res = executor.run()
        return {
            "is_successful": res.is_successful,
            "has_cycle": False,
            "completed_tasks": res.completed_tasks,
            "failed_tasks": res.failed_tasks,
            "skipped_tasks": res.skipped_tasks,
            "task_results": res.task_results,
            "tasks": get_tasks_summary(graph),
            "execution_log": execution_log
        }
    except ValueError as e:
        return {
            "is_successful": False,
            "has_cycle": True,
            "error": str(e),
            "completed_tasks": [],
            "failed_tasks": [],
            "skipped_tasks": [],
            "task_results": {},
            "tasks": get_tasks_summary(graph)
        }


def get_tasks_summary(graph: Optional[WorkflowGraph] = None) -> List[Dict[str, Any]]:
    summary = []
    current_graph = graph
    if current_graph is None:
        current_graph = WorkflowGraph()
        for tid, tinfo in task_definitions.items():
            deps = set(tinfo.get("dependencies", []))
            current_graph.add_task(Task(tid, lambda: None, dependencies=deps))

    for tid, tinfo in task_definitions.items():
        task_obj = current_graph.get_task(tid)
        status = task_obj.status.value if task_obj else "PENDING"
        err = task_obj.error if task_obj else None
        res = task_obj.result if task_obj else None
        downstream = sorted(list(current_graph.get_downstream_tasks(tid)))

        summary.append({
            "task_id": tid,
            "dependencies": sorted(tinfo.get("dependencies", [])),
            "downstream": downstream,
            "should_fail": tinfo.get("should_fail", False),
            "fail_message": tinfo.get("fail_message", ""),
            "status": status,
            "error": err,
            "result": res
        })
    return summary


# Try FastAPI first
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel

    app = FastAPI(title="TaskGraph Workflow Engine API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class TaskPayload(BaseModel):
        task_id: str
        dependencies: Optional[List[str]] = []
        should_fail: Optional[bool] = False
        fail_message: Optional[str] = "Deliberate failure"

    class TemplatePayload(BaseModel):
        template: str

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "TaskGraph Workflow Engine"}

    @app.get("/api/workflow")
    def get_workflow():
        dummy_graph = WorkflowGraph()
        for tid, tinfo in task_definitions.items():
            dummy_graph.add_task(Task(tid, lambda: None, dependencies=set(tinfo.get("dependencies", []))))
        has_cycle = dummy_graph.detect_cycles()

        return {
            "task_count": len(task_definitions),
            "has_cycle": has_cycle,
            "tasks": get_tasks_summary(dummy_graph)
        }

    @app.post("/api/workflow/tasks")
    def add_task(payload: TaskPayload):
        if not payload.task_id.strip():
            raise HTTPException(status_code=400, detail="task_id cannot be empty")
        task_definitions[payload.task_id] = {
            "dependencies": payload.dependencies or [],
            "should_fail": payload.should_fail or False,
            "fail_message": payload.fail_message or "Deliberate failure"
        }
        return {"status": "added", "task_id": payload.task_id}

    @app.delete("/api/workflow/tasks/{task_id}")
    def delete_task(task_id: str):
        if task_id in task_definitions:
            del task_definitions[task_id]
            # Clean dependencies
            for tinfo in task_definitions.values():
                if task_id in tinfo["dependencies"]:
                    tinfo["dependencies"].remove(task_id)
            return {"status": "deleted", "task_id": task_id}
        raise HTTPException(status_code=404, detail="Task not found")

    @app.post("/api/workflow/run")
    def run_workflow():
        return build_and_run_graph()

    @app.post("/api/workflow/template")
    def apply_template(payload: TemplatePayload):
        load_template(payload.template)
        return {"status": "template_applied", "template": payload.template}

    @app.post("/api/workflow/reset")
    def reset_workflow():
        load_template("default")
        return {"status": "reset"}

    def run_server(port: int = 8000):
        print(f"🚀 Starting TaskGraph Engine (FastAPI) on http://0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError:
    # Zero-dependency Fallback: Standard Library http.server
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class FallbackHTTPHandler(BaseHTTPRequestHandler):
        def _set_cors(self, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

        def do_OPTIONS(self):
            self._set_cors(200)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/health":
                self._set_cors(200)
                self.wfile.write(json.dumps({"status": "healthy", "service": "TaskGraph Workflow Engine"}).encode("utf-8"))
            elif path == "/api/workflow":
                dummy_graph = WorkflowGraph()
                for tid, tinfo in task_definitions.items():
                    dummy_graph.add_task(Task(tid, lambda: None, dependencies=set(tinfo.get("dependencies", []))))
                has_cycle = dummy_graph.detect_cycles()
                self._set_cors(200)
                self.wfile.write(json.dumps({
                    "task_count": len(task_definitions),
                    "has_cycle": has_cycle,
                    "tasks": get_tasks_summary(dummy_graph)
                }).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

        def do_POST(self):
            path = self.path.split("?")[0]
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

            if path == "/api/workflow/run":
                res = build_and_run_graph()
                self._set_cors(200)
                self.wfile.write(json.dumps(res).encode("utf-8"))

            elif path == "/api/workflow/tasks":
                tid = payload.get("task_id", "").strip()
                if not tid:
                    self._set_cors(400)
                    self.wfile.write(json.dumps({"detail": "task_id cannot be empty"}).encode("utf-8"))
                    return
                task_definitions[tid] = {
                    "dependencies": payload.get("dependencies", []),
                    "should_fail": payload.get("should_fail", False),
                    "fail_message": payload.get("fail_message", "Deliberate failure")
                }
                self._set_cors(200)
                self.wfile.write(json.dumps({"status": "added", "task_id": tid}).encode("utf-8"))

            elif path == "/api/workflow/template":
                template_name = payload.get("template", "default")
                load_template(template_name)
                self._set_cors(200)
                self.wfile.write(json.dumps({"status": "template_applied", "template": template_name}).encode("utf-8"))

            elif path == "/api/workflow/reset":
                load_template("default")
                self._set_cors(200)
                self.wfile.write(json.dumps({"status": "reset"}).encode("utf-8"))
            else:
                self._set_cors(404)
                self.wfile.write(json.dumps({"detail": f"Path {path} not found"}).encode("utf-8"))

    def run_server(port: int = 8000):
        print(f"🚀 Starting TaskGraph Engine (Standard Library HTTP Fallback) on http://0.0.0.0:{port}")
        server = HTTPServer(("0.0.0.0", port), FallbackHTTPHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)

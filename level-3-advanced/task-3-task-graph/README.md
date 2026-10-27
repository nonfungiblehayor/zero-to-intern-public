# Candidate Brief: TaskGraph Workflow Engine (BH-L3-003)

## Welcome to the TaskGraph Engineering Team

Welcome to the TaskGraph Workflow Orchestration team! Our engine powers asynchronous data pipelines and microservice workflows by scheduling tasks represented as Directed Acyclic Graphs (DAGs).

Recently, data engineering teams reported workflow anomalies during production incidents. We have triaged three critical tickets assigned to your sprint.

---

## Assigned Tickets

### Ticket #DAG-701: Downstream Dependent Tasks Fail to Cascade to SKIPPED on Upstream Failure
- **Severity:** High
- **Reporter:** Data Platform Reliability Team
- **Description:** When an upstream task fails (raises an unhandled exception), the engine marks that task as `FAILED`. However, downstream tasks that depend on it remain in `PENDING` status indefinitely. As a result, `result.skipped_tasks` is empty, and orchestrator monitoring never receives the expected skipped signals, causing pipeline status dashboards to hang.
- **Expected Behavior:** When a task fails, all downstream tasks that directly or transitively depend on the failed task must transition to `TaskStatus.SKIPPED` and be recorded in `result.skipped_tasks`.
- **Observed Behavior:** Downstream tasks remain in `TaskStatus.PENDING`, and `result.skipped_tasks` is empty.

### Ticket #DAG-702: Premature Execution in Fan-In Dependencies
- **Severity:** Critical
- **Reporter:** Financial ETL Pipeline Team
- **Description:** In fan-in workflows where a downstream task depends on multiple upstream tasks (e.g., Task C depends on Task A and Task B), Task C is observed running as soon as Task A completes, while Task B is still running or pending. This causes Task C to read incomplete inputs, corrupting daily settlement reports.
- **Expected Behavior:** A task with multiple dependencies must only be scheduled when **ALL** of its dependencies have reached `TaskStatus.COMPLETED`.
- **Observed Behavior:** The executor triggers execution as soon as *any* dependency completes.

### Ticket #DAG-703: Undetected Cycles in Disconnected / Multi-Root Graph Topologies
- **Severity:** High
- **Reporter:** Workflow Validation Service
- **Description:** Our cycle detector (`graph.detect_cycles()`) fails to detect cycles if the cyclic component does not contain a root node (a node with in-degree 0). For example, a graph containing an independent task `solo` alongside a cyclic component `X -> Y -> X` reports `detect_cycles() == False`. When the executor runs, it hangs or crashes.
- **Expected Behavior:** `detect_cycles()` must return `True` if a directed cycle exists anywhere in the graph, regardless of component topology or root connectivity.
- **Observed Behavior:** `detect_cycles()` returns `False` when the cycle is in a disconnected component without root nodes.

---

## Instructions

1. Explore the codebase under `src/`:
   - `models.py`: Task definitions, status enums, and workflow result structures.
   - `graph.py`: Workflow graph structure, dependency validation, and cycle detection.
   - `executor.py`: Topological batch execution, failure cascading, and result aggregation.
2. Run the test suite:
   ```bash
   python3 -m unittest discover tests
   ```
   Notice that the 3 reproduction tests in `tests/test_task_graph.py` currently fail.
3. Fix the defects across `src/graph.py` and `src/executor.py` (and `src/models.py` if needed).
4. Verify your fix passes all unit tests without breaking existing linear workflows.
5. Add edge-case and regression tests to `tests/test_task_graph.py` covering diamond topologies, deep transitive failure cascades, and cyclic graph rejection.
6. Fill in your technical explanation, root-cause analysis, and verification steps in `CANDIDATE_SUBMISSION.md`.

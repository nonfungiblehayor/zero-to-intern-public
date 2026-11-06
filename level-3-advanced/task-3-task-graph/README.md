# Candidate Brief: TaskGraph Workflow Engine (BH-L3-003)
**Assessment ID:** `BH-L3-003`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the TaskGraph Engineering Team

Welcome to the TaskGraph Workflow Orchestration team! Our engine powers asynchronous data pipelines and microservice workflows by scheduling tasks represented as Directed Acyclic Graphs (DAGs).

Our architecture coordinates DAG execution across layers:
- `models.py`: Task definitions, status enums, and workflow result structures.
- `graph.py`: Workflow graph structure, dependency validation, and cycle detection.
- `executor.py`: Topological batch execution, failure cascading, and result aggregation.

Recently, data engineering teams reported workflow anomalies during production incidents. We have triaged three critical tickets assigned to your sprint:
- **Ticket #DAG-701 (Upstream Failure Cascade Skip Deadlock):** When an upstream task fails, downstream tasks that depend on it remain in `PENDING` status indefinitely rather than transitioning to `SKIPPED`.
- **Ticket #DAG-702 (Premature Execution in Fan-In Dependencies):** In fan-in workflows where a downstream task depends on multiple upstream tasks (e.g., Task C depends on Task A and Task B), Task C is observed running as soon as Task A completes, while Task B is still running.
- **Ticket #DAG-703 (Undetected Cycles in Disconnected Components):** Our cycle detector (`graph.detect_cycles()`) fails to detect cycles if the cyclic component is disconnected from the first traversed node.

---

## 🚀 Running the Fullstack Application & Tests

This task is configured as a **Fullstack Application (API + React UI)** with unit tests. You can test your changes using either the interactive web console or the automated test suite.

### Option A: Interactive Workflow DAG Studio (Web UI)
1. **Launch the Backend API Server:**
   ```bash
   python3 api.py
   ```
   *Runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed, with built-in zero-dependency fallback).*

2. **Launch the Frontend Console:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*
   - Test custom DAG configurations and preset topologies (Diamond, Cascade Fail, Fan-In, Cycle).
   - Inspect visual task node cards with execution states (`COMPLETED`, `FAILED`, `SKIPPED`, `RUNNING`, `PENDING`).
   - Use the **1-Click Defect Reproduction Suite** to observe cascade skip deadlocks, premature fan-in, and disconnected cycle bypass in real time before and after your fix.

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_dag_701_upstream_failure_cascades_skipped`
- `test_bug_reproduction_ticket_dag_702_fan_in_requires_all_dependencies`
- `test_bug_reproduction_ticket_dag_703_disconnected_cycle_detection`

---

## Your Objectives

1. **Investigate Codebase:**
   - `src/models.py`: Task definitions, status enums, and workflow result structures.
   - `src/graph.py`: Workflow graph structure, dependency validation, and cycle detection (**YOUR TASK IS HERE**).
   - `src/executor.py`: Topological batch execution, failure cascading, and result aggregation (**YOUR TASK IS HERE**).

2. **Analyze Root Causes:**
   - **Failure Cascades:** Why does leaving downstream tasks in `PENDING` stall orchestrator monitoring dashboards? How should recursive cascading traverse transitive descendants?
   - **Fan-In Conjunction:** Why is `any()` mathematically flawed for prerequisite dependency resolution?
   - **Multi-Component Cycle Traversal:** Why does a single DFS from `next(iter(self._tasks))` miss cycles in disconnected graph components?

3. **Implement the Fix:**
   - In `src/graph.py`:
     - In `detect_cycles()`, loop over all task IDs in `self._tasks`. If an unvisited task is found, trigger DFS. Use 3-state tracking (`visited` and recursion stack `rec_stack`).
   - In `src/executor.py`:
     - Change the dependency check for ready tasks from `any()` to `all(dep in completed for dep in task.dependencies)`.
     - When a task fails, recursively cascade `TaskStatus.SKIPPED` to all direct and transitive downstream tasks, recording them in `skipped_tasks`.
   - In `src/models.py` / `src/graph.py`:
     - Ensure empty task IDs raise `ValueError`.

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_task_graph.py` covering:
     - Diamond topologies with multiple fan-out and fan-in stages.
     - Deep transitive failure cascades (4+ tiers).
     - Partial failure in independent branches without impacting healthy branches.
     - Cyclic workflow rejection during execution.

5. **Prepare for Technical Defense:**
   - Be prepared to discuss topological sorting algorithms (Kahn's algorithm vs DFS), cycle detection complexity, failure domain isolation, and distributed DAG orchestration (e.g., Airflow, Temporal) during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only.
- Do not alter public method signatures or dataclass definitions.
- Demonstrate clean engineering practices, graph algorithm correctness, and robust error handling.

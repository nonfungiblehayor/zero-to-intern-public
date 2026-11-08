"""
TaskGraph Workflow Executor.
"""
from typing import Dict, List, Set, Optional

try:
    from .models import Task, TaskStatus, WorkflowResult
    from .graph import WorkflowGraph
except ImportError:
    from models import Task, TaskStatus, WorkflowResult
    from graph import WorkflowGraph


class WorkflowExecutor:
    def __init__(self, graph: WorkflowGraph):
        self.graph = graph

    def run(self) -> WorkflowResult:
        if self.graph.detect_cycles():
            raise ValueError("Cannot execute workflow containing cyclic dependencies")

        tasks = self.graph.get_all_tasks()
        completed: Set[str] = set()
        failed: Set[str] = set()
        skipped: Set[str] = set()
        task_results: Dict[str, any] = {}

        # Reset task statuses
        for task in tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.error = None

        while True:
            # Find tasks ready to execute
            ready_tasks = []
            for task in tasks.values():
                if task.status != TaskStatus.PENDING:
                    continue

                if not task.dependencies:
                    ready_tasks.append(task)
                elif any(dep in completed for dep in task.dependencies):
                    ready_tasks.append(task)

            if not ready_tasks:
                break

            # Execute ready tasks
            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                try:
                    result = task.fn()
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    completed.add(task.task_id)
                    task_results[task.task_id] = result
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    failed.add(task.task_id)


        is_success = len(failed) == 0 and len(completed) == len(tasks)
        return WorkflowResult(
            is_successful=is_success,
            completed_tasks=sorted(list(completed)),
            failed_tasks=sorted(list(failed)),
            skipped_tasks=sorted(list(skipped)),
            task_results=task_results,
        )

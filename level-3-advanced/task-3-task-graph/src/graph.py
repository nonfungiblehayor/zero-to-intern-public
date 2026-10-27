"""
TaskGraph Directed Acyclic Graph (DAG) Structure & Cycle Detection.
"""
from typing import Dict, List, Set, Optional

try:
    from .models import Task
except ImportError:
    from models import Task


class WorkflowGraph:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        # Adjacency list: task_id -> set of task_ids that directly depend on it (downstream)
        self._downstream: Dict[str, Set[str]] = {}

    def add_task(self, task: Task) -> None:
        if task.task_id in self._tasks:
            raise ValueError(f"Task with ID {task.task_id} already exists")
        self._tasks[task.task_id] = task
        if task.task_id not in self._downstream:
            self._downstream[task.task_id] = set()

        for dep_id in task.dependencies:
            if dep_id not in self._downstream:
                self._downstream[dep_id] = set()
            self._downstream[dep_id].add(task.task_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Task]:
        return dict(self._tasks)

    def get_downstream_tasks(self, task_id: str) -> Set[str]:
        return set(self._downstream.get(task_id, set()))

    def detect_cycles(self) -> bool:
        """
        Returns True if the workflow contains a directed cycle, False otherwise.
        """
        # DEFECT (Ticket #DAG-703): Only runs DFS from the first task!
        # If the graph has multiple disconnected components or a cycle in a separate
        # component, this returns False (false negative cycle detection).
        if not self._tasks:
            return False

        first_task_id = next(iter(self._tasks.keys()))
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self._downstream.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        return dfs(first_task_id)

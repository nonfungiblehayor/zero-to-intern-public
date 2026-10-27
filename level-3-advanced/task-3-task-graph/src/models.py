"""
TaskGraph Workflow Engine Domain Models.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class Task:
    task_id: str
    fn: Callable[[], Any]
    dependencies: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    is_successful: bool
    completed_tasks: List[str]
    failed_tasks: List[str]
    skipped_tasks: List[str]
    task_results: Dict[str, Any] = field(default_factory=dict)

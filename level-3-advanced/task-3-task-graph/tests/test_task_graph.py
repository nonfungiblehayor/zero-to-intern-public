"""
Unit tests for TaskGraph DAG Workflow Engine.
"""
import unittest
import os
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import Task, TaskStatus
from graph import WorkflowGraph
from executor import WorkflowExecutor


class TestTaskGraph(unittest.TestCase):
    def test_basic_linear_workflow(self):
        """Sequential tasks A -> B execute in order and capture results."""
        graph = WorkflowGraph()
        execution_order = []

        def task_a():
            execution_order.append("A")
            return 10

        def task_b():
            execution_order.append("B")
            return 20

        graph.add_task(Task("A", task_a))
        graph.add_task(Task("B", task_b, dependencies={"A"}))

        executor = WorkflowExecutor(graph)
        res = executor.run()

        self.assertTrue(res.is_successful)
        self.assertEqual(execution_order, ["A", "B"])
        self.assertEqual(res.task_results["A"], 10)
        self.assertEqual(res.task_results["B"], 20)

    def test_bug_reproduction_ticket_dag_701_upstream_failure_cascades_skipped(self):
        """
        REPRODUCTION TEST 1 (Ticket #DAG-701):
        When upstream task A fails, downstream dependent tasks B and C
        must be marked SKIPPED and included in result.skipped_tasks.
        They must not be left hanging in PENDING!
        """
        graph = WorkflowGraph()

        def fail_fn():
            raise RuntimeError("Database connection failed")

        def downstream_fn():
            return "Should not run"

        graph.add_task(Task("extract", fail_fn))
        graph.add_task(Task("transform", downstream_fn, dependencies={"extract"}))
        graph.add_task(Task("load", downstream_fn, dependencies={"transform"}))

        executor = WorkflowExecutor(graph)
        res = executor.run()

        self.assertFalse(res.is_successful)
        self.assertEqual(res.failed_tasks, ["extract"])
        self.assertIn(
            "transform", res.skipped_tasks,
            "Downstream task was not marked as SKIPPED after upstream failure!"
        )
        self.assertIn(
            "load", res.skipped_tasks,
            "Transitive downstream task was not marked as SKIPPED after upstream failure!"
        )

    def test_bug_reproduction_ticket_dag_702_fan_in_requires_all_dependencies(self):
        """
        REPRODUCTION TEST 2 (Ticket #DAG-702):
        Fan-In Dependency: Task C depends on BOTH A and B.
        Task C must ONLY execute after BOTH A and B have completed.
        """
        graph = WorkflowGraph()
        completed_order = []

        # A is fast/independent. B requires X first. C depends on A and B.
        graph.add_task(Task("A", lambda: completed_order.append("A")))
        # Register C before B so any() triggers C before B is even ready
        def task_c():
            self.assertIn("A", completed_order, "Task C executed before A finished!")
            self.assertIn("B", completed_order, "Premature fan-in! Task C executed before B finished!")
            completed_order.append("C")

        graph.add_task(Task("C", task_c, dependencies={"A", "B"}))
        graph.add_task(Task("X", lambda: completed_order.append("X")))
        graph.add_task(Task("B", lambda: completed_order.append("B"), dependencies={"X"}))

        executor = WorkflowExecutor(graph)
        res = executor.run()
        self.assertTrue(res.is_successful)
        self.assertEqual(completed_order[-1], "C")

    def test_bug_reproduction_ticket_dag_703_disconnected_cycle_detection(self):
        """
        REPRODUCTION TEST 3 (Ticket #DAG-703):
        Cycle detection must find cycles across all components,
        not just the first registered node.
        """
        graph = WorkflowGraph()
        # Component 1: Linear independent task
        graph.add_task(Task("solo", lambda: 1))

        # Component 2: Cyclic subgraph X -> Y -> X
        graph.add_task(Task("X", lambda: 2, dependencies={"Y"}))
        graph.add_task(Task("Y", lambda: 3, dependencies={"X"}))

        has_cycle = graph.detect_cycles()
        self.assertTrue(
            has_cycle,
            "Failed to detect cycle in disconnected component!"
        )


if __name__ == "__main__":
    unittest.main()

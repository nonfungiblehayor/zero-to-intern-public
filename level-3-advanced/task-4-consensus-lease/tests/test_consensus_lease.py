import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from clock import SimulatedClock
from network import SimulatedNetwork
from node import ConsensusNode
from lease_manager import ClusterLeaseManager
from models import LeaseGrant


class TestConsensusLease(unittest.TestCase):
    def setUp(self):
        self.clock = SimulatedClock(start_ms=1000)
        self.network = SimulatedNetwork()
        self.manager = ClusterLeaseManager(self.clock, self.network, rtt_latency_ms=50)

    def test_baseline_cluster_lease_acquisition(self):
        """Baseline: In a 3-node cluster, a single candidate acquires a lease."""
        for name in ["node-1", "node-2", "node-3"]:
            self.manager.add_node(ConsensusNode(name, self.clock))

        grant = self.manager.acquire_lease("node-1", "lock:db-migrations", duration_ms=1000)
        self.assertIsNotNone(grant)
        self.assertEqual(grant.leader_id, "node-1")
        self.assertTrue(self.manager.is_lease_valid("lock:db-migrations", "node-1"))

    def test_bug_reproduction_ticket_lease_801_split_brain_quorum_calculation(self):
        """
        REPRODUCTION TEST 1 (Ticket #LEASE-801):
        In a 5-node cluster partitioned into {N1, N2} and {N3, N4, N5}:
        Quorum must be strict majority (3/5).
        Node 1 in the minority partition (2/5) MUST NOT be granted the lease!
        """
        for i in range(1, 6):
            self.manager.add_node(ConsensusNode(f"N{i}", self.clock))

        # Check quorum calculation directly
        self.assertEqual(
            self.manager.get_quorum_size(), 3,
            "Quorum size for 5 nodes must be 3, not 2!"
        )

        # Network partition: {N1, N2} isolated from {N3, N4, N5}
        self.network.partition({"N1", "N2"}, {"N3", "N4", "N5"})

        grant_minority = self.manager.acquire_lease("N1", "resource:catalog", duration_ms=1000)
        self.assertIsNone(
            grant_minority,
            "Split-brain vulnerability! Minority partition (2 of 5) was granted the lease!"
        )

        grant_majority = self.manager.acquire_lease("N3", "resource:catalog", duration_ms=1000)
        self.assertIsNotNone(
            grant_majority,
            "Majority partition (3 of 5) should have acquired the lease!"
        )

    def test_bug_reproduction_ticket_lease_802_ballot_rejection_livelock(self):
        """
        REPRODUCTION TEST 2 (Ticket #LEASE-802):
        When a peer node rejects a proposal because it has seen a higher ballot (e.g. 50),
        the candidate must adopt the higher ballot so that the very next attempt succeeds.
        """
        n1 = ConsensusNode("N1", self.clock)
        n2 = ConsensusNode("N2", self.clock)
        n3 = ConsensusNode("N3", self.clock)

        # Peer N2 and N3 already promised ballot 50 to an earlier leader
        n2.highest_promised_ballot["resource:queue"] = 50
        n3.highest_promised_ballot["resource:queue"] = 50

        self.manager.add_node(n1)
        self.manager.add_node(n2)
        self.manager.add_node(n3)

        # First attempt: N1 starts at ballot 1, rejected by N2 and N3
        first_try = self.manager.acquire_lease("N1", "resource:queue", duration_ms=1000)
        self.assertIsNone(first_try)

        # Second attempt: N1 must have adopted the higher ballot (> 50) and succeed
        second_try = self.manager.acquire_lease("N1", "resource:queue", duration_ms=1000)
        self.assertIsNotNone(
            second_try,
            "Election livelock! Candidate failed to adopt higher peer ballot on retry."
        )
        self.assertGreater(second_try.ballot, 50)

    def test_bug_reproduction_ticket_lease_803_lease_expiry_rtt_skew(self):
        """
        REPRODUCTION TEST 3 (Ticket #LEASE-803):
        Lease duration is 1000ms with 200ms RTT latency.
        The lease is requested at T=1000.
        Peers accept at T=1000 and promise until T=2000.
        The candidate must NOT extend its lease validity past T=2000!
        """
        self.manager.rtt_latency_ms = 200

        n1 = ConsensusNode("N1", self.clock)
        n2 = ConsensusNode("N2", self.clock)
        n3 = ConsensusNode("N3", self.clock)

        self.manager.add_node(n1)
        self.manager.add_node(n2)
        self.manager.add_node(n3)

        # Acquire at T=1000. RTT is 200ms, so clock reaches 1200ms when grant returns.
        grant = self.manager.acquire_lease("N1", "resource:lock", duration_ms=1000)
        self.assertIsNotNone(grant)

        # Advance clock to T=2050 (past 2000ms expiration boundary)
        self.clock.advance_ms(850)  # Current time is 1200 + 850 = 2050ms

        # Leader N1 must consider the lease EXPIRED at 2050ms
        self.assertFalse(
            self.manager.is_lease_valid("resource:lock", "N1"),
            "Lease overlap vulnerability! Leader still considers lease valid after peer expiration!"
        )


if __name__ == "__main__":
    unittest.main()

from typing import Dict, Optional, List
try:
    from .models import LeaseProposal, LeaseVote, LeaseGrant, LeaseState
    from .clock import SimulatedClock
    from .network import SimulatedNetwork
    from .node import ConsensusNode
except ImportError:
    from models import LeaseProposal, LeaseVote, LeaseGrant, LeaseState
    from clock import SimulatedClock
    from network import SimulatedNetwork
    from node import ConsensusNode


class ClusterLeaseManager:
    def __init__(
        self,
        clock: SimulatedClock,
        network: SimulatedNetwork,
        rtt_latency_ms: int = 50
    ):
        self.clock = clock
        self.network = network
        self.rtt_latency_ms = rtt_latency_ms
        self.nodes: Dict[str, ConsensusNode] = {}
        self.local_ballots: Dict[str, int] = {}
        self.active_leases: Dict[str, LeaseGrant] = {}

    def add_node(self, node: ConsensusNode):
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node
        self.local_ballots[node.node_id] = 0

    def get_quorum_size(self) -> int:
        """
        Calculate required quorum size for consensus.
        """
        # BUG (Ticket #LEASE-801): Uses integer division total // 2 instead of strict majority.
        # In a 5-node cluster, 5 // 2 == 2, allowing split-brain if partitioned into 2 and 3!
        return len(self.nodes) // 2

    def acquire_lease(
        self,
        candidate_id: str,
        resource: str,
        duration_ms: int = 1000
    ) -> Optional[LeaseGrant]:
        if candidate_id not in self.nodes:
            raise ValueError(f"Unknown candidate node: {candidate_id}")
        if not resource:
            raise ValueError("Resource cannot be empty")
        if duration_ms <= 0:
            raise ValueError("duration_ms must be positive")

        start_time = self.clock.now_ms()

        # Generate proposal ballot
        ballot = self.local_ballots.get(candidate_id, 0) + 1
        self.local_ballots[candidate_id] = ballot

        proposal = LeaseProposal(
            resource=resource,
            candidate_id=candidate_id,
            ballot=ballot,
            duration_ms=duration_ms
        )

        votes: List[LeaseVote] = []
        for peer_id, peer_node in self.nodes.items():
            if self.network.can_communicate(candidate_id, peer_id):
                vote = peer_node.handle_proposal(proposal)
                votes.append(vote)

        # Simulate network RTT latency
        if self.rtt_latency_ms > 0:
            self.clock.advance_ms(self.rtt_latency_ms)

        granted_votes = [v for v in votes if v.granted]
        quorum = self.get_quorum_size()

        if len(granted_votes) >= quorum:
            # BUG (Ticket #LEASE-803): Computes lease grant starting from clock AFTER RTT transit,
            # ignoring that peers accepted the promise starting from start_time!
            # Leader will hold lease past peer expiration window.
            grant = LeaseGrant(
                resource=resource,
                leader_id=candidate_id,
                ballot=ballot,
                granted_at_ms=self.clock.now_ms(),  # BUGGY: should be start_time
                duration_ms=duration_ms
            )

            # Broadcast grant to reachable nodes
            for peer_id, peer_node in self.nodes.items():
                if self.network.can_communicate(candidate_id, peer_id):
                    peer_node.record_grant(grant)

            self.active_leases[resource] = grant
            return grant
        else:
            # BUG (Ticket #LEASE-802): When rejected, fails to adopt peer's higher ballot.
            # Next attempt will increment only by +1 from candidate's local ballot,
            # causing livelock against peers with higher ballots.
            return None

    def is_lease_valid(self, resource: str, leader_id: str) -> bool:
        grant = self.active_leases.get(resource)
        if not grant:
            return False
        if grant.leader_id != leader_id:
            return False
        return self.clock.now_ms() < grant.expires_at_ms

    def get_lease(self, resource: str) -> Optional[LeaseGrant]:
        return self.active_leases.get(resource)

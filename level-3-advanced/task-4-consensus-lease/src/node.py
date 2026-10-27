from typing import Optional, Dict
try:
    from .models import LeaseProposal, LeaseVote, LeaseGrant
    from .clock import SimulatedClock
except ImportError:
    from models import LeaseProposal, LeaseVote, LeaseGrant
    from clock import SimulatedClock


class ConsensusNode:
    def __init__(self, node_id: str, clock: SimulatedClock):
        if not node_id or not isinstance(node_id, str):
            raise ValueError("node_id must be a non-empty string")
        self.node_id = node_id
        self.clock = clock
        self.highest_promised_ballot: Dict[str, int] = {}
        self.active_leases: Dict[str, LeaseGrant] = {}

    def handle_proposal(self, proposal: LeaseProposal) -> LeaseVote:
        res = proposal.resource
        curr_promised = self.highest_promised_ballot.get(res, 0)
        curr_lease = self.active_leases.get(res)
        now = self.clock.now_ms()

        # If active unexpired lease held by another node with >= ballot:
        if curr_lease and now < curr_lease.expires_at_ms:
            if curr_lease.leader_id != proposal.candidate_id and proposal.ballot <= curr_lease.ballot:
                return LeaseVote(
                    voter_id=self.node_id,
                    granted=False,
                    ballot=proposal.ballot,
                    highest_seen_ballot=max(curr_promised, curr_lease.ballot),
                    reason=f"Active lease held by {curr_lease.leader_id} until {curr_lease.expires_at_ms}"
                )

        if proposal.ballot > curr_promised:
            self.highest_promised_ballot[res] = proposal.ballot
            return LeaseVote(
                voter_id=self.node_id,
                granted=True,
                ballot=proposal.ballot,
                highest_seen_ballot=proposal.ballot,
                reason="Proposal accepted"
            )
        else:
            return LeaseVote(
                voter_id=self.node_id,
                granted=False,
                ballot=proposal.ballot,
                highest_seen_ballot=curr_promised,
                reason=f"Ballot {proposal.ballot} <= highest promised {curr_promised}"
            )

    def record_grant(self, grant: LeaseGrant):
        self.active_leases[grant.resource] = grant

    def get_lease(self, resource: str) -> Optional[LeaseGrant]:
        return self.active_leases.get(resource)

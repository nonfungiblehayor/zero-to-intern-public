from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class LeaseState(Enum):
    FREE = "FREE"
    HELD = "HELD"
    EXPIRED = "EXPIRED"


@dataclass
class LeaseProposal:
    resource: str
    candidate_id: str
    ballot: int
    duration_ms: int


@dataclass
class LeaseVote:
    voter_id: str
    granted: bool
    ballot: int
    highest_seen_ballot: int
    reason: str = ""


@dataclass
class LeaseGrant:
    resource: str
    leader_id: str
    ballot: int
    granted_at_ms: int
    duration_ms: int

    @property
    def expires_at_ms(self) -> int:
        return self.granted_at_ms + self.duration_ms

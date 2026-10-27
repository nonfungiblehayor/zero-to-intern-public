# Candidate Brief: ConsensusLease Manager (BH-L3-004)

## Welcome to the ConsensusLease Engineering Team

Welcome to the Distributed Core Infrastructure team! Our `ConsensusLease` coordinator manages distributed leader leases across multi-node clusters to ensure mutual exclusion for database writers and background orchestrators.

Recently, our site reliability team detected dual-leader split-brain events during cross-datacenter fiber cuts and election stalls during network healing. Three critical tickets have been assigned to your sprint.

---

## Assigned Tickets

### Ticket #LEASE-801: Split-Brain from Quorum Calculation
- **Severity:** Critical
- **Reporter:** Site Reliability Engineering
- **Description:** During a network partition in a 5-node cluster that separated nodes into `{N1, N2}` and `{N3, N4, N5}`, Node 1 was able to acquire a lease for `resource:catalog` while Node 3 simultaneously acquired a lease for the same resource. Both nodes operated as active leaders at the same time, producing severe data inconsistency.
- **Expected Behavior:** In any cluster of $N$ nodes, acquiring a lease must require a strict majority of nodes: $Q = \lfloor N / 2 \rfloor + 1$. In a 5-node cluster, quorum must be 3. The minority partition (2 nodes) must fail to acquire the lease.
- **Observed Behavior:** `get_quorum_size()` returns 2 for a 5-node cluster (`5 // 2 == 2`), granting the lease to minority partitions.

### Ticket #LEASE-802: Election Livelock on Ballot Rejection
- **Severity:** High
- **Reporter:** Distributed Database Team
- **Description:** When an election candidate encounters peers that have already promised higher ballot numbers (e.g., ballot 50 from a partitioned leader), the candidate is rejected. On subsequent retries, the candidate increments only its own local ballot (`1 -> 2 -> 3`), failing repeatedly and entering an election livelock.
- **Expected Behavior:** Upon ballot rejection, the candidate must discover the highest ballot seen by its peers and adopt that ballot (`ballot = max(local, highest_peer)`) so that its next retry uses `highest_peer + 1`.
- **Observed Behavior:** Candidate increments only by `+1` from its outdated local ballot, livelocking the election.

### Ticket #LEASE-803: Lease Expiry Overlap from RTT Transit Skew
- **Severity:** High
- **Reporter:** Distributed Consensus Validation Team
- **Description:** Leaders calculate lease expiration as `clock.now_ms() + duration_ms` after receiving quorum votes. However, network transit took $RTT$ milliseconds. Because peers accepted the proposal at $T_{start}$, their promise expires at $T_{start} + duration\_ms$. The leader continues to consider its lease valid until $T_{start} + RTT + duration\_ms$. During the $RTT$ window, peers grant a new lease to another node, causing dual-leader overlap.
- **Expected Behavior:** The leader's lease grant expiration must not extend past the peer promise boundary. Lease validity must be anchored to $T_{start}$ (when the proposal was initiated) or discount the elapsed round-trip time.
- **Observed Behavior:** Leader extends lease validity past peer expiration by $RTT$ milliseconds.

---

## Instructions

1. Explore the codebase under `src/`:
   - `models.py`: Lease proposals, votes, and grant definitions.
   - `clock.py`: Deterministic simulated clock (`SimulatedClock`).
   - `network.py`: Simulated partitionable network (`SimulatedNetwork`).
   - `node.py`: `ConsensusNode` promise and grant logic.
   - `lease_manager.py`: `ClusterLeaseManager` coordinator.
2. Run the test suite:
   ```bash
   python3 -m unittest discover tests
   ```
   Notice that the 3 reproduction tests fail.
3. Fix the defects in `src/lease_manager.py`.
4. Verify all tests pass cleanly without breaking baseline single-candidate behavior.
5. Author regression tests covering edge cases (even-node clusters, single-node clusters, node recovery).
6. Fill in your technical explanation and mathematical justifications in `CANDIDATE_SUBMISSION.md`.

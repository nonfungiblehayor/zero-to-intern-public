import React, { useState, useEffect } from 'react';
import {
  Shield,
  Clock,
  Network,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Play,
  RotateCcw,
  Zap,
  Radio,
  Lock,
  Unlock,
  FastForward,
  Cpu,
  Layers,
  ChevronRight,
  Split,
  Activity
} from 'lucide-react';

export default function App() {
  const [clusterState, setClusterState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states
  const [candidateId, setCandidateId] = useState('N1');
  const [resource, setResource] = useState('resource:catalog');
  const [durationMs, setDurationMs] = useState(1000);
  const [acquiring, setAcquiring] = useState(false);
  const [acquireResult, setAcquireResult] = useState(null);

  // Partition form
  const [groupA, setGroupA] = useState(['N1', 'N2']);
  const [groupB, setGroupB] = useState(['N3', 'N4', 'N5']);

  // Clock jump
  const [clockDelta, setClockDelta] = useState(100);

  // Reproduce result
  const [reproResult, setReproResult] = useState(null);
  const [reproLoading, setReproLoading] = useState(false);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/cluster/state');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setClusterState(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Cannot connect to ConsensusLease API. Make sure api.py is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleAcquireLease = async (e) => {
    if (e) e.preventDefault();
    setAcquiring(true);
    setAcquireResult(null);
    try {
      const res = await fetch('/api/lease/acquire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          resource,
          duration_ms: parseInt(durationMs, 10)
        })
      });
      const data = await res.json();
      setAcquireResult(data);
      await fetchState();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setAcquiring(false);
    }
  };

  const handleAdvanceClock = async (delta) => {
    try {
      await fetch('/api/clock/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta_ms: delta })
      });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreatePartition = async () => {
    try {
      await fetch('/api/network/partition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_a: groupA, group_b: groupB })
      });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleHealNetwork = async () => {
    try {
      await fetch('/api/network/heal', { method: 'POST' });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleDrop = async (nodeId, isCurrentlyDropped) => {
    const endpoint = isCurrentlyDropped ? '/api/network/recover' : '/api/network/drop';
    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: nodeId })
      });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResetCluster = async () => {
    try {
      await fetch('/api/cluster/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: ['N1', 'N2', 'N3', 'N4', 'N5'],
          rtt_latency_ms: 50,
          start_ms: 1000
        })
      });
      setReproResult(null);
      setAcquireResult(null);
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReproduce = async (ticketId) => {
    setReproLoading(true);
    setReproResult(null);
    try {
      const res = await fetch(`/api/reproduce/${ticketId}`, { method: 'POST' });
      const data = await res.json();
      setReproResult(data);
      await fetchState();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setReproLoading(false);
    }
  };

  if (loading && !clusterState) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem' }}>
        <RefreshCw size={36} className="animate-spin" style={{ color: 'var(--accent-blue)' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Connecting to ConsensusLease Cluster Simulator...</p>
      </div>
    );
  }

  const nodes = clusterState?.nodes || [];
  const network = clusterState?.network || { partitions: [], dropped_nodes: [], connectivity: {} };
  const clusterLeases = Object.values(clusterState?.cluster_leases || {});
  const isSplitBrainVulnerable = clusterState && clusterState.quorum_size <= Math.floor(clusterState.total_nodes / 2);

  // Group partition helper
  const getNodePartitionGroup = (nodeId) => {
    for (let i = 0; i < network.partitions.length; i++) {
      const p = network.partitions[i];
      if (p.group_a.includes(nodeId)) return { label: `Part-A (#${i + 1})`, color: 'cyan' };
      if (p.group_b.includes(nodeId)) return { label: `Part-B (#${i + 1})`, color: 'purple' };
    }
    return { label: 'Online', color: 'emerald' };
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Navbar */}
      <header className="glass-panel" style={{ padding: '1.25rem 1.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)' }}>
            <Radio size={24} style={{ color: '#fff' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #60a5fa, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                ConsensusLease Studio
              </h1>
              <span className="badge badge-purple">LEVEL 3 DISTRIBUTED</span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
              Paxos-Style Quorum Coordinator, Network Partitions & Split-Brain Simulator
            </p>
          </div>
        </div>

        {/* Global Cluster Metrics */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
          {/* Virtual Clock */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <Clock size={16} style={{ color: 'var(--accent-cyan)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Virtual Clock</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8' }}>
                T = {clusterState?.clock_ms ?? 0} ms
              </div>
            </div>
          </div>

          {/* Quorum Size */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <Shield size={16} style={{ color: isSplitBrainVulnerable ? 'var(--accent-rose)' : 'var(--accent-emerald)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Consensus Quorum</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: isSplitBrainVulnerable ? '#fda4af' : '#6ee7b7' }}>
                {clusterState?.quorum_size} / {clusterState?.total_nodes} nodes
                {isSplitBrainVulnerable && <span style={{ fontSize: '0.7rem', marginLeft: 4, color: '#f43f5e' }}>(BUG!)</span>}
              </div>
            </div>
          </div>

          {/* RTT Latency */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <Activity size={16} style={{ color: 'var(--accent-amber)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>RTT Latency</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fcd34d' }}>
                {clusterState?.rtt_latency_ms} ms
              </div>
            </div>
          </div>

          {/* Reset button */}
          <button id="btn-cluster-reset" className="btn btn-secondary" onClick={handleResetCluster} title="Reset cluster to pristine initial state">
            <RotateCcw size={15} />
            Reset Cluster
          </button>
        </div>
      </header>

      {/* Error alert */}
      {error && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: 10, padding: '0.9rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fda4af' }}>
          <AlertTriangle size={20} />
          <div style={{ flex: 1, fontSize: '0.875rem' }}>{error}</div>
          <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Defect Reproduction Control Deck */}
      <section className="glass-panel" style={{ padding: '1.25rem 1.5rem', borderLeft: '4px solid #6366f1' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Zap size={18} style={{ color: 'var(--accent-indigo)' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Fault Injection & Defect Reproduction Test Benches
            </h2>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            One-click execution against live consensus state machine
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {/* Ticket 801 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-rose">#LEASE-801</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Partition Split-Brain</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Quorum Integer Division Defect
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Partitions 5 nodes into {'{N1,N2}'} vs {'{N3,N4,N5}'}. Demonstrates concurrent lease grants if quorum is calculated as <code>N // 2 == 2</code> instead of strict majority (3).
              </p>
            </div>
            <button
              id="btn-repro-lease-801"
              className="btn btn-danger"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('LEASE-801')}
            >
              <Split size={14} />
              Reproduce #LEASE-801
            </button>
          </div>

          {/* Ticket 802 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-amber">#LEASE-802</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Election Livelock</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Peer Higher Ballot Non-Adoption
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Peers N2 & N3 have promised ballot 50. Candidate N1 proposes ballot 1. On rejection, candidate fails to adopt peer ballot 50, causing livelock against higher peers.
              </p>
            </div>
            <button
              id="btn-repro-lease-802"
              className="btn btn-amber"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('LEASE-802')}
            >
              <RotateCcw size={14} />
              Reproduce #LEASE-802
            </button>
          </div>

          {/* Ticket 803 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-blue">#LEASE-803</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Lease Expiry Skew</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                RTT Latency Transit Inflation
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                With 200ms RTT, leader stamps grant at clock after RTT transit instead of start_time, holding lease past peer promise window and risking dual-leader overlap.
              </p>
            </div>
            <button
              id="btn-repro-lease-803"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('LEASE-803')}
            >
              <FastForward size={14} />
              Reproduce #LEASE-803
            </button>
          </div>
        </div>

        {/* Reproduce Output Banner */}
        {reproResult && (
          <div style={{
            marginTop: '1.25rem',
            padding: '1.25rem',
            borderRadius: 10,
            background: reproResult.verdict.startsWith('CLEAN') ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
            border: `1px solid ${reproResult.verdict.startsWith('CLEAN') ? 'rgba(16, 185, 129, 0.35)' : 'rgba(244, 63, 94, 0.35)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                {reproResult.verdict.startsWith('CLEAN') ? (
                  <CheckCircle size={22} style={{ color: '#10b981' }} />
                ) : (
                  <XCircle size={22} style={{ color: '#f43f5e' }} />
                )}
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: reproResult.verdict.startsWith('CLEAN') ? '#6ee7b7' : '#fda4af' }}>
                  {reproResult.ticket}: {reproResult.description}
                </span>
              </div>
              <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={() => setReproResult(null)}>
                Clear
              </button>
            </div>

            <p style={{ fontSize: '0.875rem', lineHeight: 1.5, color: '#f8fafc' }}>
              {reproResult.verdict}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 8 }}>
              {reproResult.ticket === '#LEASE-801' && (
                <>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Quorum Calculated</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                      {reproResult.quorum_calculated}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Minority {'{N1,N2}'} Grant</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.partition_minority_result.success ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                      {reproResult.partition_minority_result.success ? 'GRANTED (Defect!)' : 'REJECTED (Safe)'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Majority {'{N3,N4,N5}'} Grant</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: 700 }}>
                      {reproResult.partition_majority_result.success ? 'GRANTED' : 'REJECTED'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Split Brain State</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.split_brain_detected ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                      {reproResult.split_brain_detected ? 'ACTIVE SPLIT-BRAIN' : 'NONE (Safe Consensus)'}
                    </div>
                  </div>
                </>
              )}

              {reproResult.ticket === '#LEASE-802' && (
                <>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Attempt 1 Result</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                      {reproResult.first_attempt?.success ? 'Granted' : 'Rejected'} (Ballot {reproResult.first_attempt?.ballot})
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Attempt 2 Result</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: reproResult.second_attempt?.success ? '#10b981' : '#f43f5e' }}>
                      {reproResult.second_attempt?.success ? 'Granted' : 'Rejected'} (Ballot {reproResult.second_attempt?.ballot})
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Adopted Higher Ballot</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: reproResult.adopted_higher_ballot ? '#10b981' : '#f43f5e' }}>
                      {reproResult.adopted_higher_ballot ? 'YES (>50)' : 'NO (<=50)'}
                    </div>
                  </div>
                </>
              )}

              {reproResult.ticket === '#LEASE-803' && (
                <>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Clock At Evaluation</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                      T = {reproResult.clock_ms} ms
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Leader Lease Valid?</div>
                    <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: reproResult.leader_lease_valid ? '#f43f5e' : '#10b981' }}>
                      {reproResult.leader_lease_valid ? 'VALID (Overlap Risk!)' : 'EXPIRED (Correct)'}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Main Grid: Interactive Cluster Nodes Topology */}
      <section className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Cpu size={20} style={{ color: 'var(--accent-cyan)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Cluster Node Topology & Consensus State
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Advance Virtual Clock:</span>
            {[50, 200, 500, 1000].map((d) => (
              <button
                key={d}
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.55rem', fontSize: '0.75rem' }}
                onClick={() => handleAdvanceClock(d)}
                title={`Advance virtual clock by +${d}ms`}
              >
                +{d}ms
              </button>
            ))}
          </div>
        </div>

        {/* Nodes Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          {nodes.map((node) => {
            const partitionInfo = getNodePartitionGroup(node.node_id);
            const isDropped = node.is_dropped;
            const leasesHeld = Object.entries(node.active_leases || {});

            return (
              <div
                key={node.node_id}
                style={{
                  background: isDropped ? 'rgba(30, 41, 59, 0.4)' : 'rgba(15, 23, 42, 0.7)',
                  border: `2px solid ${
                    isDropped
                      ? 'rgba(244, 63, 94, 0.4)'
                      : partitionInfo.color === 'cyan'
                      ? 'rgba(6, 182, 212, 0.6)'
                      : partitionInfo.color === 'purple'
                      ? 'rgba(168, 85, 247, 0.6)'
                      : 'rgba(255, 255, 255, 0.08)'
                  }`,
                  borderRadius: 12,
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  opacity: isDropped ? 0.65 : 1,
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: isDropped ? '#f43f5e' : 'var(--accent-blue)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.9rem'
                    }}>
                      {node.node_id}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Node {node.node_id}</div>
                      <div style={{ fontSize: '0.7rem', color: isDropped ? '#fda4af' : 'var(--text-muted)' }}>
                        {isDropped ? 'Dropped (Isolated)' : 'Connected'}
                      </div>
                    </div>
                  </div>

                  <span className={`badge badge-${isDropped ? 'rose' : partitionInfo.color === 'cyan' ? 'blue' : partitionInfo.color === 'purple' ? 'purple' : 'emerald'}`}>
                    {isDropped ? 'OFFLINE' : partitionInfo.label}
                  </span>
                </div>

                {/* State metrics */}
                <div style={{ background: 'rgba(0, 0, 0, 0.35)', padding: '0.6rem 0.85rem', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.775rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Local Ballot:</span>
                    <span className="code-font" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      #{node.local_ballot}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Promised Ballots:</span>
                    <span className="code-font" style={{ fontWeight: 600 }}>
                      {Object.keys(node.highest_promised_ballot || {}).length > 0 ? (
                        Object.entries(node.highest_promised_ballot).map(([r, b]) => `${r.split(':')[1] || r}: #${b}`).join(', ')
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>none</span>
                      )}
                    </span>
                  </div>
                </div>

                {/* Leases held by this node */}
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
                    Active Grants ({leasesHeld.length})
                  </div>
                  {leasesHeld.length === 0 ? (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      No active resource leases
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {leasesHeld.map(([res, grant]) => (
                        <div key={res} style={{
                          background: grant.is_valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                          border: `1px solid ${grant.is_valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                          padding: '0.4rem 0.65rem',
                          borderRadius: 6,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.75rem'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            {grant.is_valid ? <Lock size={12} style={{ color: '#10b981' }} /> : <Unlock size={12} style={{ color: '#f43f5e' }} />}
                            <span style={{ fontWeight: 600 }}>{res}</span>
                          </div>
                          <span className="code-font" style={{ color: grant.is_valid ? '#6ee7b7' : '#fda4af' }}>
                            {grant.is_valid ? `exp @ ${grant.expires_at_ms}ms` : 'EXPIRED'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Node quick actions */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ flex: 1, padding: '0.4rem 0.6rem', fontSize: '0.75rem' }}
                    onClick={() => {
                      setCandidateId(node.node_id);
                    }}
                    title="Select this node as lease candidate in form below"
                  >
                    Select
                  </button>
                  <button
                    className={`btn ${isDropped ? 'btn-emerald' : 'btn-danger'}`}
                    style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem' }}
                    onClick={() => handleToggleDrop(node.node_id, isDropped)}
                    title={isDropped ? 'Recover dropped node' : 'Drop node from network'}
                  >
                    {isDropped ? 'Recover' : 'Drop'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Two Column Layout: Lease Acquisition Console & Active Leases + Network Partitioner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '1.5rem' }}>
        {/* Left: Lease Acquisition Console */}
        <section className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Layers size={18} style={{ color: 'var(--accent-blue)' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Request Distributed Lease
            </h2>
          </div>

          <form onSubmit={handleAcquireLease} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>
                  Candidate Node
                </label>
                <select
                  id="select-candidate-id"
                  className="input-field"
                  style={{ width: '100%', cursor: 'pointer' }}
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                >
                  {nodes.map((n) => (
                    <option key={n.node_id} value={n.node_id}>
                      Node {n.node_id} {n.is_dropped ? '(DROPPED)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>
                  Duration (ms)
                </label>
                <input
                  id="input-duration-ms"
                  type="number"
                  className="input-field"
                  style={{ width: '100%' }}
                  value={durationMs}
                  onChange={(e) => setDurationMs(e.target.value)}
                  min="50"
                  step="50"
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>
                Resource Identifier
              </label>
              <input
                id="input-resource-name"
                type="text"
                className="input-field"
                style={{ width: '100%' }}
                value={resource}
                onChange={(e) => setResource(e.target.value)}
                placeholder="e.g. resource:catalog, lock:db-migrations"
                required
              />
              <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
                {['resource:catalog', 'resource:queue', 'resource:lock', 'lock:db-migrations'].map((r) => (
                  <button
                    key={r}
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                    onClick={() => setResource(r)}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            <button
              id="btn-acquire-lease"
              type="submit"
              className="btn btn-primary"
              style={{ marginTop: '0.5rem', padding: '0.75rem' }}
              disabled={acquiring}
            >
              {acquiring ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
              Execute Lease Acquisition Protocol
            </button>
          </form>

          {/* Acquire Result Display */}
          {acquireResult && (
            <div style={{
              padding: '1rem',
              borderRadius: 8,
              background: acquireResult.success ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
              border: `1px solid ${acquireResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              fontSize: '0.85rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                {acquireResult.success ? <CheckCircle size={18} style={{ color: '#10b981' }} /> : <XCircle size={18} style={{ color: '#f43f5e' }} />}
                <span style={{ fontWeight: 700, color: acquireResult.success ? '#6ee7b7' : '#fda4af' }}>
                  {acquireResult.success ? 'Lease Acquisition Succeeded' : 'Lease Acquisition Rejected'}
                </span>
              </div>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{acquireResult.message}</p>
              {acquireResult.grant && (
                <div className="code-font" style={{ fontSize: '0.75rem', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: 6 }}>
                  Leader: {acquireResult.grant.leader_id} | Ballot: #{acquireResult.grant.ballot} | Granted At: {acquireResult.grant.granted_at_ms}ms | Expires At: {acquireResult.grant.expires_at_ms}ms
                </div>
              )}
            </div>
          )}

          {/* Active Cluster Leases Table */}
          <div style={{ marginTop: '0.5rem' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
              Cluster Master Leases ({clusterLeases.length})
            </h3>
            {clusterLeases.length === 0 ? (
              <div style={{ padding: '1.25rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.825rem', background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                No active leases recorded in the cluster.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {clusterLeases.map((l) => (
                  <div
                    key={l.resource}
                    style={{
                      background: 'rgba(15, 23, 42, 0.6)',
                      border: `1px solid ${l.is_valid ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.3)'}`,
                      borderRadius: 8,
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="badge badge-purple">{l.leader_id}</span>
                        <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{l.resource}</span>
                      </div>
                      <span className={`badge badge-${l.is_valid ? 'emerald' : 'rose'}`}>
                        {l.is_valid ? 'VALID LEASE' : 'EXPIRED'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <span>Ballot: #{l.ballot}</span>
                      <span>Duration: {l.duration_ms}ms</span>
                      <span className="code-font">Expires: {l.expires_at_ms}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Right: Network Fault Injection & Connectivity Matrix */}
        <section className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Network size={18} style={{ color: 'var(--accent-purple)' }} />
              <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Network Partition & Interconnect Studio
              </h2>
            </div>
            <button className="btn btn-emerald" style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }} onClick={handleHealNetwork}>
              <RotateCcw size={14} />
              Heal Network
            </button>
          </div>

          {/* Partition Builder */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Isolate Nodes into Mutually Partitioned Subsets:
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              {/* Group A */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.4rem' }}>
                  Group A Nodes
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {nodes.map((n) => {
                    const isSelected = groupA.includes(n.node_id);
                    return (
                      <button
                        key={n.node_id}
                        type="button"
                        className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        onClick={() => {
                          if (isSelected) setGroupA(groupA.filter((id) => id !== n.node_id));
                          else setGroupA([...groupA, n.node_id]);
                        }}
                      >
                        {n.node_id}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Group B */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-purple)', marginBottom: '0.4rem' }}>
                  Group B Nodes
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {nodes.map((n) => {
                    const isSelected = groupB.includes(n.node_id);
                    return (
                      <button
                        key={n.node_id}
                        type="button"
                        className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        onClick={() => {
                          if (isSelected) setGroupB(groupB.filter((id) => id !== n.node_id));
                          else setGroupB([...groupB, n.node_id]);
                        }}
                      >
                        {n.node_id}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <button
              id="btn-apply-partition"
              className="btn btn-secondary"
              style={{ width: '100%', border: '1px solid var(--accent-purple)' }}
              onClick={handleCreatePartition}
            >
              <Split size={14} />
              Isolate Group A From Group B
            </button>
          </div>

          {/* Active Partitions List */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Active Partitions ({network.partitions.length})
            </div>
            {network.partitions.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <CheckCircle size={14} /> All nodes have unrestricted network communication.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {network.partitions.map((p, idx) => (
                  <div key={idx} style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: 6, padding: '0.5rem 0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                    <span>
                      Partition #{idx + 1}: {'{' + p.group_a.join(', ') + '}'} ⇎ {'{' + p.group_b.join(', ') + '}'}
                    </span>
                    <span className="badge badge-rose">BLOCKED</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Connectivity Matrix */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.6rem' }}>
              Full Peer-to-Peer Interconnect Matrix
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '0.4rem', color: 'var(--text-muted)', textAlign: 'left' }}>Src \ Dst</th>
                    {nodes.map((n) => (
                      <th key={n.node_id} style={{ padding: '0.4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {n.node_id}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {nodes.map((src) => (
                    <tr key={src.node_id} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '0.4rem', fontWeight: 700, color: 'var(--text-secondary)' }}>{src.node_id}</td>
                      {nodes.map((dst) => {
                        const canTalk = network.connectivity[src.node_id]?.[dst.node_id];
                        return (
                          <td key={dst.node_id} style={{ padding: '0.4rem', textAlign: 'center' }}>
                            {src.node_id === dst.node_id ? (
                              <span style={{ color: 'var(--text-muted)' }}>•</span>
                            ) : canTalk ? (
                              <span style={{ color: '#10b981', fontWeight: 700 }}>✓</span>
                            ) : (
                              <span style={{ color: '#f43f5e', fontWeight: 700 }}>✗</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>

      {/* Cluster Activity Event Log */}
      <section className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h2 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Consensus Protocol Audit Trail
            </h2>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Latest {clusterState?.history?.length || 0} transitions recorded
          </span>
        </div>

        <div style={{ maxHeight: 200, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {(clusterState?.history || []).slice().reverse().map((item, idx) => (
            <div
              key={idx}
              className="code-font"
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                padding: '0.45rem 0.75rem',
                borderRadius: 6,
                fontSize: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: `3px solid ${
                  item.action === 'ACQUIRE_LEASE'
                    ? item.success
                      ? '#10b981'
                      : '#f43f5e'
                    : item.action.includes('PARTITION')
                    ? '#a855f7'
                    : '#3b82f6'
                }`
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span className="badge badge-blue" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>
                  {item.action}
                </span>
                <span>{item.message || JSON.stringify(item)}</span>
              </div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                T = {item.clock_ms ?? item.clock_after ?? item.new_clock_ms ?? 0} ms
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import {
  Layers,
  Database,
  Search,
  Plus,
  RotateCcw,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  TrendingDown,
  Trash2,
  FileText,
  Sliders,
  Compass,
  ArrowRight,
  ShieldAlert,
  Ghost,
  Sparkles
} from 'lucide-react';

export default function App() {
  const [streamState, setStreamState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selection for compaction
  const [selectedSegmentIds, setSelectedSegmentIds] = useState([]);
  const [compacting, setCompacting] = useState(false);

  // Append record form
  const [appendKey, setAppendKey] = useState('');
  const [appendValue, setAppendValue] = useState('');
  const [isTombstone, setIsTombstone] = useState(false);
  const [appending, setAppending] = useState(false);

  // Lookup form
  const [searchKey, setSearchKey] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [searching, setSearching] = useState(false);

  // Consumer watermark update
  const [watermarkConsumer, setWatermarkConsumer] = useState('consumer:indexer-lagging');
  const [watermarkOffset, setWatermarkOffset] = useState(2);

  // Reproduce result
  const [reproResult, setReproResult] = useState(null);
  const [reproLoading, setReproLoading] = useState(false);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/stream/state');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStreamState(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Cannot connect to StreamCompactor API. Make sure api.py is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleAppend = async (e) => {
    if (e) e.preventDefault();
    if (!appendKey) return;
    setAppending(true);
    try {
      const res = await fetch('/api/stream/append', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: appendKey,
          value: isTombstone ? null : appendValue
        })
      });
      const data = await res.json();
      setStreamState(data);
      setAppendKey('');
      setAppendValue('');
      setIsTombstone(false);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setAppending(false);
    }
  };

  const handleCompact = async () => {
    if (selectedSegmentIds.length === 0) return;
    setCompacting(true);
    try {
      const res = await fetch('/api/stream/compact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment_ids: selectedSegmentIds })
      });
      const data = await res.json();
      setStreamState(data);
      setSelectedSegmentIds([]);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setCompacting(false);
    }
  };

  const handleLookup = async (e) => {
    if (e) e.preventDefault();
    if (!searchKey) return;
    setSearching(true);
    try {
      const res = await fetch(`/api/stream/lookup/${encodeURIComponent(searchKey)}`);
      const data = await res.json();
      setLookupResult(data);
    } catch (err) {
      console.error(err);
      setLookupResult({ found: false, error: err.message });
    } finally {
      setSearching(false);
    }
  };

  const handleUpdateWatermark = async (e) => {
    if (e) e.preventDefault();
    try {
      const res = await fetch('/api/stream/watermark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          consumer_id: watermarkConsumer,
          offset: parseInt(watermarkOffset, 10)
        })
      });
      const data = await res.json();
      setStreamState(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  const handleResetStream = async () => {
    try {
      const res = await fetch('/api/stream/reset', { method: 'POST' });
      const data = await res.json();
      setStreamState(data);
      setReproResult(null);
      setLookupResult(null);
      setSelectedSegmentIds([]);
    } catch (err) {
      console.error(err);
      setError(err.message);
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

  const toggleSelectSegment = (segId) => {
    if (selectedSegmentIds.includes(segId)) {
      setSelectedSegmentIds(selectedSegmentIds.filter((id) => id !== segId));
    } else {
      setSelectedSegmentIds([...selectedSegmentIds, segId]);
    }
  };

  if (loading && !streamState) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem' }}>
        <RefreshCw size={36} className="animate-spin" style={{ color: 'var(--accent-emerald)' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Connecting to StreamCompactor Engine...</p>
      </div>
    );
  }

  const segments = streamState?.segments || [];
  const consumerWatermarks = streamState?.consumer_watermarks || {};
  const materializedState = streamState?.materialized_state || {};
  const safeWatermark = streamState?.safe_compaction_watermark ?? 0;

  // Check if watermark is calculated buggily (i.e. is max instead of min)
  const watermarkValues = Object.values(consumerWatermarks);
  const isWatermarkBuggy = watermarkValues.length > 1 && safeWatermark === Math.max(...watermarkValues);

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header */}
      <header className="glass-panel" style={{ padding: '1.25rem 1.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(16, 185, 129, 0.4)' }}>
            <Layers size={24} style={{ color: '#fff' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #34d399, #38bdf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                StreamCompactor Studio
              </h1>
              <span className="badge badge-emerald">LEVEL 3 STORAGE</span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
              Partitioned Log Compaction, Tombstone Preservation & Sparse Index Engine
            </p>
          </div>
        </div>

        {/* Global Stream Metrics */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
          {/* Safe Watermark */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <TrendingDown size={16} style={{ color: isWatermarkBuggy ? 'var(--accent-rose)' : 'var(--accent-emerald)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Safe Compaction Watermark</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: isWatermarkBuggy ? '#fda4af' : '#6ee7b7' }}>
                Offset &le; {safeWatermark}
                {isWatermarkBuggy && <span style={{ fontSize: '0.7rem', marginLeft: 4, color: '#f43f5e' }}>(BUG!)</span>}
              </div>
            </div>
          </div>

          {/* Total Segments */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <Database size={16} style={{ color: 'var(--accent-blue)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Partition Segments</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#93c5fd' }}>
                {segments.length} segments
              </div>
            </div>
          </div>

          {/* Total Records */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.4rem 0.85rem', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
            <FileText size={16} style={{ color: 'var(--accent-purple)' }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Total Records</div>
              <div className="code-font" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#d8b4fe' }}>
                {streamState?.total_records} events
              </div>
            </div>
          </div>

          <button id="btn-stream-reset" className="btn btn-secondary" onClick={handleResetStream} title="Reset partition log to default state">
            <RotateCcw size={15} />
            Reset Stream
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

      {/* Defect Reproduction Deck */}
      <section className="glass-panel" style={{ padding: '1.25rem 1.5rem', borderLeft: '4px solid #10b981' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Zap size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Fault Injection & Defect Reproduction Test Benches
            </h2>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            One-click execution against live log partition compactor
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {/* Ticket 901 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-rose">#STREAM-901</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ghost Resurrection</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Premature Tombstone Purge
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Purges tombstones during compaction without checking older uncompacted segments. Deleted keys resurrect upon log replay!
              </p>
            </div>
            <button
              id="btn-repro-stream-901"
              className="btn btn-danger"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('STREAM-901')}
            >
              <Ghost size={14} />
              Reproduce #STREAM-901
            </button>
          </div>

          {/* Ticket 902 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-amber">#STREAM-902</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Watermark Regression</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Inverted Max/Min Reduction
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Uses <code>max()</code> instead of <code>min()</code> across consumer offsets. Fast consumers advance safe watermark ahead of lagging consumers, causing data loss.
              </p>
            </div>
            <button
              id="btn-repro-stream-902"
              className="btn btn-amber"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('STREAM-902')}
            >
              <TrendingDown size={14} />
              Reproduce #STREAM-902
            </button>
          </div>

          {/* Ticket 903 */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-blue">#STREAM-903</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Index Offset Skew</span>
              </div>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Corrupted Sparse Index (IndexError)
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Stores raw log offset (e.g. 50) instead of array position (0..N) in compacted segment index, crashing point lookups with <code>IndexError</code>.
              </p>
            </div>
            <button
              id="btn-repro-stream-903"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={reproLoading}
              onClick={() => handleReproduce('STREAM-903')}
            >
              <Compass size={14} />
              Reproduce #STREAM-903
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

            {reproResult.ticket === '#STREAM-901' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Tombstone Retained in Segment</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.tombstone_retained_in_compacted ? '#10b981' : '#f43f5e', fontWeight: 700 }}>
                    {reproResult.tombstone_retained_in_compacted ? 'YES (Protected)' : 'NO (Purged Prematurely)'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Ghost Record Resurrected</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.resurrected ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                    {reproResult.resurrected ? 'YES: user1 = Alice' : 'NO: user1 deleted'}
                  </div>
                </div>
              </div>
            )}

            {reproResult.ticket === '#STREAM-902' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Consumer Fast Offset</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>{reproResult.consumer_fast}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Consumer Lagging Offset</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>{reproResult.consumer_lagging}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Calculated Safe Watermark</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.safe_watermark_calculated === 500 ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                    Offset {reproResult.safe_watermark_calculated}
                  </div>
                </div>
              </div>
            )}

            {reproResult.ticket === '#STREAM-903' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Index Offset Entry</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>{reproResult.index_entry}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Compacted Array Length</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>{reproResult.compacted_records_len}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Lookup Status</div>
                  <div className="code-font" style={{ fontSize: '0.85rem', color: reproResult.error ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                    {reproResult.error ? `CRASH: ${reproResult.error}` : `OK: ${reproResult.lookup_result}`}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Main Stream Segments Visualizer */}
      <section className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Database size={20} style={{ color: 'var(--accent-emerald)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Partition Log Segments & Record Offsets
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              id="btn-compact-selected"
              className="btn btn-primary"
              disabled={selectedSegmentIds.length === 0 || compacting}
              onClick={handleCompact}
            >
              {compacting ? <RefreshCw size={15} className="animate-spin" /> : <Sparkles size={15} />}
              Compact Selected Segments ({selectedSegmentIds.length})
            </button>
          </div>
        </div>

        {/* Segments horizontal container */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {segments.map((seg) => {
            const isSelected = selectedSegmentIds.includes(seg.segment_id);

            return (
              <div
                key={seg.segment_id}
                style={{
                  background: seg.is_compacted ? 'rgba(99, 102, 241, 0.1)' : 'rgba(15, 23, 42, 0.7)',
                  border: `2px solid ${
                    isSelected
                      ? 'var(--accent-emerald)'
                      : seg.is_compacted
                      ? 'rgba(99, 102, 241, 0.4)'
                      : 'rgba(255, 255, 255, 0.08)'
                  }`,
                  borderRadius: 12,
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)'
                }}
              >
                {/* Segment Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelectSegment(seg.segment_id)}
                      style={{ cursor: 'pointer', width: 16, height: 16, accentColor: 'var(--accent-emerald)' }}
                    />
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.95rem' }}>
                        Segment #{seg.segment_id}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Offsets: [{seg.start_offset}..{seg.end_offset}] &bull; {seg.record_count} records
                      </div>
                    </div>
                  </div>

                  <span className={`badge ${seg.is_compacted ? 'badge-purple' : 'badge-blue'}`}>
                    {seg.is_compacted ? 'COMPACTED' : 'ACTIVE LOG'}
                  </span>
                </div>

                {/* Records list */}
                <div style={{ maxHeight: 220, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {seg.records.map((r) => (
                    <div
                      key={r.offset}
                      style={{
                        background: r.is_tombstone ? 'rgba(239, 68, 68, 0.1)' : 'rgba(0, 0, 0, 0.35)',
                        border: `1px solid ${r.is_tombstone ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.05)'}`,
                        borderRadius: 6,
                        padding: '0.45rem 0.65rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '0.75rem'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="code-font" style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                          #{r.offset}
                        </span>
                        <span className="code-font" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                          {r.key}
                        </span>
                      </div>

                      {r.is_tombstone ? (
                        <span className="badge badge-tombstone" style={{ fontSize: '0.65rem' }}>
                          🪦 TOMBSTONE
                        </span>
                      ) : (
                        <span className="code-font" style={{ color: '#34d399', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          "{r.value}"
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                {/* Segment index footer */}
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.5rem' }}>
                  Indexed Keys: {Object.keys(seg.index || {}).length}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Two-Column Utility Deck: Append & Lookup vs Watermarks & Materialized State */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '1.5rem' }}>
        {/* Left: Append & Key Lookup */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Append Event Record Form */}
          <section className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
              <Plus size={18} style={{ color: 'var(--accent-emerald)' }} />
              <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Append Event to Log Partition
              </h2>
            </div>

            <form onSubmit={handleAppend} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>
                  Event Key
                </label>
                <input
                  id="input-event-key"
                  type="text"
                  className="input-field"
                  style={{ width: '100%' }}
                  placeholder="e.g. user:alice, config:theme, sensor:temp"
                  value={appendKey}
                  onChange={(e) => setAppendKey(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>
                  Event Payload Value
                </label>
                <input
                  id="input-event-value"
                  type="text"
                  className="input-field"
                  style={{ width: '100%', opacity: isTombstone ? 0.4 : 1 }}
                  placeholder="e.g. active, dark, 26.5C"
                  value={appendValue}
                  onChange={(e) => setAppendValue(e.target.value)}
                  disabled={isTombstone}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  id="checkbox-is-tombstone"
                  type="checkbox"
                  checked={isTombstone}
                  onChange={(e) => setIsTombstone(e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: 'var(--accent-rose)', cursor: 'pointer' }}
                />
                <label htmlFor="checkbox-is-tombstone" style={{ fontSize: '0.8rem', color: '#fda4af', fontWeight: 600, cursor: 'pointer' }}>
                  Emit as Tombstone Deletion (null value)
                </label>
              </div>

              <button
                id="btn-append-event"
                type="submit"
                className="btn btn-primary"
                style={{ marginTop: '0.25rem' }}
                disabled={appending}
              >
                {appending ? <RefreshCw size={15} className="animate-spin" /> : <Plus size={15} />}
                Append to Log Partition
              </button>
            </form>
          </section>

          {/* Point Record Lookup */}
          <section className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
              <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
              <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Point Record Lookup via Sparse Index
              </h2>
            </div>

            <form onSubmit={handleLookup} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <input
                id="input-search-key"
                type="text"
                className="input-field"
                style={{ flex: 1 }}
                placeholder="Lookup key (e.g. user:alice, device:1)"
                value={searchKey}
                onChange={(e) => setSearchKey(e.target.value)}
                required
              />
              <button id="btn-search-key" type="submit" className="btn btn-secondary" disabled={searching}>
                {searching ? <RefreshCw size={15} className="animate-spin" /> : <Search size={15} />}
                Lookup
              </button>
            </form>

            {lookupResult && (
              <div style={{
                padding: '0.85rem 1rem',
                borderRadius: 8,
                background: lookupResult.corrupted
                  ? 'rgba(244, 63, 94, 0.15)'
                  : lookupResult.found
                  ? 'rgba(16, 185, 129, 0.12)'
                  : 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${
                  lookupResult.corrupted
                    ? 'rgba(244, 63, 94, 0.35)'
                    : lookupResult.found
                    ? 'rgba(16, 185, 129, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                fontSize: '0.85rem'
              }}>
                {lookupResult.corrupted ? (
                  <div style={{ color: '#fda4af' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                      <AlertTriangle size={16} /> Index Corruption Error!
                    </div>
                    <div>{lookupResult.error}</div>
                  </div>
                ) : lookupResult.found ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span className="code-font" style={{ fontWeight: 700, color: '#38bdf8' }}>{lookupResult.key}</span>
                      <span className="code-font" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Offset #{lookupResult.record.offset}</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Value: <span className="code-font" style={{ color: lookupResult.record.is_tombstone ? '#fda4af' : '#34d399' }}>
                        {lookupResult.record.is_tombstone ? '🪦 TOMBSTONE' : `"${lookupResult.record.value}"`}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No record found for key "{searchKey}".
                  </div>
                )}
              </div>
            )}
          </section>
        </div>

        {/* Right: Watermarks & Materialized State */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Consumer Watermarks Console */}
          <section className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
              <Sliders size={18} style={{ color: 'var(--accent-amber)' }} />
              <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Consumer Watermark Controller
              </h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
              {Object.entries(consumerWatermarks).map(([consumer, offset]) => {
                const isBottleneck = offset === Math.min(...Object.values(consumerWatermarks));

                return (
                  <div
                    key={consumer}
                    style={{
                      background: 'rgba(15, 23, 42, 0.6)',
                      border: `1px solid ${isBottleneck ? 'rgba(245, 158, 11, 0.4)' : 'var(--border-subtle)'}`,
                      borderRadius: 8,
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{consumer}</div>
                      <div style={{ fontSize: '0.7rem', color: isBottleneck ? '#fcd34d' : 'var(--text-muted)' }}>
                        {isBottleneck ? 'Bottleneck (Safest Watermark Limit)' : 'Active Consumer'}
                      </div>
                    </div>
                    <span className="code-font badge badge-amber">
                      Offset {offset}
                    </span>
                  </div>
                );
              })}
            </div>

            <form onSubmit={handleUpdateWatermark} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <input
                id="input-watermark-consumer"
                type="text"
                className="input-field"
                style={{ flex: 1, minWidth: 160 }}
                value={watermarkConsumer}
                onChange={(e) => setWatermarkConsumer(e.target.value)}
                placeholder="Consumer ID"
                required
              />
              <input
                id="input-watermark-offset"
                type="number"
                className="input-field"
                style={{ width: 100 }}
                value={watermarkOffset}
                onChange={(e) => setWatermarkOffset(e.target.value)}
                min="0"
                required
              />
              <button id="btn-update-watermark" type="submit" className="btn btn-secondary">
                Set Offset
              </button>
            </form>
          </section>

          {/* Materialized Key-Value View */}
          <section className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Compass size={18} style={{ color: 'var(--accent-purple)' }} />
                <h2 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Materialized Key-Value State
                </h2>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {Object.keys(materializedState).length} active keys
              </span>
            </div>

            {Object.keys(materializedState).length === 0 ? (
              <div style={{ padding: '1.25rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.825rem', background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                Partition state is currently empty.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', maxHeight: 220, overflowY: 'auto' }}>
                {Object.entries(materializedState).map(([k, v]) => (
                  <div
                    key={k}
                    style={{
                      background: 'rgba(15, 23, 42, 0.6)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '0.5rem 0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.8rem'
                    }}
                  >
                    <span className="code-font" style={{ fontWeight: 700, color: '#38bdf8' }}>{k}</span>
                    <span className="code-font" style={{ color: '#34d399' }}>"{v}"</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

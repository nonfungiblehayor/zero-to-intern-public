import React, { useState, useEffect } from 'react'

export default function App() {
  const [metricsList, setMetricsList] = useState(['api_latency_ms', 'cpu_utilization'])
  const [selectedMetric, setSelectedMetric] = useState('api_latency_ms')
  const [windowSeconds, setWindowSeconds] = useState(60)
  const [startTime, setStartTime] = useState(0.0)
  const [endTime, setEndTime] = useState(300.0)
  const [fillEmptyWindows, setFillEmptyWindows] = useState(true)

  // Aggregation results
  const [buckets, setBuckets] = useState([])
  const [totalPoints, setTotalPoints] = useState(0)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  // Ingest form
  const [ingestTimestamp, setIngestTimestamp] = useState(60.0)
  const [ingestValue, setIngestValue] = useState(75.0)

  // 1-Click Diagnostics Suite
  const [scenarioState, setScenarioState] = useState({
    running: false,
    name: null,
    logs: [],
    status: null // 'vulnerable' | 'fixed' | 'error'
  })

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const fetchAggregation = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: selectedMetric,
          start_time: Number(startTime),
          end_time: Number(endTime),
          window_seconds: Number(windowSeconds),
          fill_empty_windows: fillEmptyWindows
        })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Aggregation failed')

      setBuckets(data.buckets || [])

      // Update state overview
      const stateRes = await fetch('/api/state')
      if (stateRes.ok) {
        const sData = await stateRes.json()
        setTotalPoints(sData.total_points || 0)
        setMetricsList(Object.keys(sData.metrics || {}))
      }
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAggregation()
  }, [selectedMetric, windowSeconds, fillEmptyWindows])

  const handleIngestPoint = async (e) => {
    if (e) e.preventDefault()
    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: selectedMetric,
          timestamp: Number(ingestTimestamp),
          value: Number(ingestValue)
        })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Ingestion failed')

      showToast(`Sample ingested at t=${ingestTimestamp}s (val: ${ingestValue})`, 'success')
      await fetchAggregation()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleReset = async () => {
    try {
      await fetch('/api/reset', { method: 'POST' })
      showToast('Telemetry aggregator reset to default demo', 'info')
      setScenarioState({ running: false, name: null, logs: [], status: null })
      await fetchAggregation()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  // 1-Click Diagnostic Suites
  const runScenarioMet501 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #MET-501: Boundary Fence-Post Trap',
      logs: ['[INIT] Ingesting test sample at exact boundary t = 60.0s...'],
      status: null
    })

    try {
      // Ingest test point at exactly 60.0s
      await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: 'test_fencepost',
          timestamp: 60.0,
          value: 99.0
        })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ Ingested test point: timestamp=60.0, value=99.0`,
          `[ACTION] Aggregating metric across [0.0, 120.0) with 60s windows...`
        ]
      }))

      // Aggregate [0, 120) with window=60
      const res = await fetch('/api/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: 'test_fencepost',
          start_time: 0.0,
          end_time: 120.0,
          window_seconds: 60,
          fill_empty_windows: true
        })
      })
      const data = await res.json()
      const b0 = data.buckets.find(b => b.start_time === 0.0)
      const b1 = data.buckets.find(b => b.start_time === 60.0)

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Window [0.0, 60.0) count: ${b0 ? b0.count : 0}`,
          `Window [60.0, 120.0) count: ${b1 ? b1.count : 0}`
        ]
      }))

      // Standard half-open interval rule: 60.0 belongs to [60, 120), NOT [0, 60)
      if (b0 && b0.count > 0) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Window [0, 60) included point at 60.0!`,
            `ROOT CAUSE: Aggregator used inclusive comparison (<= window.end_time) instead of half-open interval window.contains(timestamp)!`
          ]
        }))
      } else if (b1 && b1.count === 1) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Point at 60.0s correctly placed in [60.0, 120.0) and excluded from [0.0, 60.0).`,
            `SUCCESS: Half-open boundary alignment confirmed.`
          ]
        }))
      }
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  const runScenarioMet502 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #MET-502: Timeline Window Gap Suppression',
      logs: ['[INIT] Testing zero-filled continuous timeline generation across quiet periods...'],
      status: null
    })

    try {
      // Ingest points at 10.0s and 150.0s with gap [60, 120)
      await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric_name: 'test_gap', timestamp: 10.0, value: 50.0 })
      })
      await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric_name: 'test_gap', timestamp: 150.0, value: 60.0 })
      })

      // Aggregate [0, 180) with window=60, fill_empty_windows=True
      const res = await fetch('/api/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: 'test_gap',
          start_time: 0.0,
          end_time: 180.0,
          window_seconds: 60,
          fill_empty_windows: true
        })
      })
      const data = await res.json()
      const totalWindows = data.buckets?.length || 0

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Expected windows count: 3 ([0, 60), [60, 120), [120, 180))`,
          `Actual windows returned: ${totalWindows}`
        ]
      }))

      if (totalWindows < 3) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Quiet window [60, 120) was completely omitted from output list!`,
            `ROOT CAUSE: Aggregator silently drops empty windows even when fill_empty_windows=True, causing broken/jagged dashboard timelines.`
          ]
        }))
      } else {
        const quietWin = data.buckets.find(b => b.start_time === 60.0)
        if (quietWin && quietWin.count === 0 && quietWin.avg === 0) {
          setScenarioState(prev => ({
            ...prev,
            running: false,
            status: 'fixed',
            logs: [
              ...prev.logs,
              `🛡️ PROTECTED! Continuous timeline preserved with zero-filled bucket: count=0, avg=0.0.`,
              `SUCCESS: Zero-filling contract verified.`
            ]
          }))
        }
      }
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  const runScenarioMet503 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #MET-503: P95 Percentile On Unsorted Samples',
      logs: ['[INIT] Ingesting 20 samples in random unsorted order with high tail values...'],
      status: null
    })

    try {
      // Ingest 20 samples with values 1 to 20 shuffled
      const shuffledVals = [20, 1, 15, 3, 19, 4, 18, 5, 17, 2, 16, 6, 14, 7, 13, 8, 12, 9, 11, 10]
      for (let i = 0; i < shuffledVals.length; i++) {
        await fetch('/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            metric_name: 'test_p95_order',
            timestamp: 10.0 + i,
            value: shuffledVals[i]
          })
        })
      }

      const res = await fetch('/api/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_name: 'test_p95_order',
          start_time: 0.0,
          end_time: 60.0,
          window_seconds: 60
        })
      })
      const data = await res.json()
      const bucket = data.buckets?.[0]
      const p95 = bucket?.p95

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Expected P95 (95th percentile of 1..20): >= 19.0`,
          `Actual P95 returned: ${p95}`
        ]
      }))

      if (p95 < 19.0) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Computed P95 is ${p95} (expected >= 19.0)!`,
            `ROOT CAUSE: Aggregator indexed into unsorted values array (values[idx]) rather than sorted array (sorted(values)[idx])!`
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! P95 correctly computed on sorted distribution: ${p95}.`,
            `SUCCESS: Sorting before rank selection confirmed.`
          ]
        }))
      }
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  // Visual calculations
  const maxAvgInBuckets = Math.max(...buckets.map(b => b.avg), 1)

  return (
    <div className="app-container">
      {/* Toast */}
      {toast && (
        <div className={`toast-notification toast-${toast.type}`}>
          {toast.type === 'success' && '✓ '}
          {toast.type === 'error' && '✕ '}
          {toast.type === 'warning' && '⚠ '}
          {toast.type === 'info' && 'ℹ '}
          {toast.message}
        </div>
      )}

      {/* Header */}
      <header className="top-header">
        <div className="header-left">
          <div className="brand-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3v18h18" />
              <path d="M18 9l-5 5-4-4-6 6" />
            </svg>
          </div>
          <div>
            <div className="brand-title-wrap">
              <h1>CloudMetric Telemetry Studio</h1>
              <span className="badge-level">BH-L2-005</span>
              <span className="badge-env">INTERMEDIATE</span>
            </div>
            <p className="brand-subtitle">
              Time-Series Aggregation Engine • Contiguous Bucketing & Percentile Observability
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn btn-outline" onClick={fetchAggregation} disabled={loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            Refresh
          </button>
          <button className="btn btn-danger-outline" onClick={handleReset}>
            Reset Telemetry
          </button>
        </div>
      </header>

      {/* Metric Cards Overview */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Active Metric</div>
          <div className="metric-value text-cyan" style={{ fontSize: '1.4rem', textTransform: 'none' }}>
            {selectedMetric}
          </div>
          <div className="metric-foot">{totalPoints} total ingested points</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Windows Generated</div>
          <div className="metric-value text-indigo">{buckets.length}</div>
          <div className="metric-foot">{windowSeconds}s downsampling interval</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Quiet Windows (Zero-Fill)</div>
          <div className="metric-value text-amber">{buckets.filter(b => b.count === 0).length}</div>
          <div className="metric-foot">Traffic gaps preserved</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Peak P95 Value</div>
          <div className="metric-value text-emerald">
            {buckets.length > 0 ? Math.max(...buckets.map(b => b.p95)).toFixed(1) : '0.0'}
          </div>
          <div className="metric-foot">95th percentile upper bound</div>
        </div>
      </div>

      {/* Main Grid: Diagnostics & Live Aggregator Controls */}
      <div className="dashboard-grid">
        {/* Left Column: Diagnostics & Ingestion */}
        <div className="column">
          <div className="card">
            <div className="card-header">
              <h2>⚡ 1-Click Defect Reproduction Suite</h2>
              <span className="card-badge">Observability Diagnostics</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Diagnose known defects across half-open boundaries, empty window omission, and unsorted percentile calculations.
              </p>

              <div className="scenario-buttons">
                <button
                  className="scenario-btn"
                  onClick={runScenarioMet501}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-red"></span>
                    Ticket #MET-501: Boundary Fence-Post Trap
                  </div>
                  <div className="scenario-btn-desc">
                    Tests whether a point at exactly 60.0s is misclassified into [0, 60) instead of [60, 120).
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioMet502}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-amber"></span>
                    Ticket #MET-502: Timeline Window Gap Suppression
                  </div>
                  <div className="scenario-btn-desc">
                    Checks whether windows with 0 samples are silently dropped or properly zero-filled.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioMet503}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-cyan"></span>
                    Ticket #MET-503: P95 On Unsorted Array
                  </div>
                  <div className="scenario-btn-desc">
                    Evaluates nearest-rank percentile computation on a randomized array of latency samples.
                  </div>
                </button>
              </div>

              {/* Terminal Log */}
              {scenarioState.name && (
                <div className={`scenario-terminal status-${scenarioState.status || 'running'}`}>
                  <div className="terminal-header">
                    <span>Diagnostic Log: {scenarioState.name}</span>
                    <span className="terminal-badge">{scenarioState.status?.toUpperCase() || 'RUNNING'}</span>
                  </div>
                  <div className="terminal-body">
                    {scenarioState.logs.map((log, idx) => (
                      <div key={idx} className="terminal-line">{log}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Ingest Telemetry Sample */}
          <div className="card">
            <div className="card-header">
              <h2>📥 Ingest Custom Telemetry Point</h2>
              <span className="card-badge">POST /api/ingest</span>
            </div>
            <div className="card-body">
              <form onSubmit={handleIngestPoint}>
                <div className="form-group">
                  <label>Timestamp (seconds)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={ingestTimestamp}
                    onChange={(e) => setIngestTimestamp(e.target.value)}
                    className="text-input mono"
                  />
                  <span className="input-hint">Tip: Try entering 60.0, 120.0, or 180.0 to test boundary alignment.</span>
                </div>

                <div className="form-group">
                  <label>Observed Metric Value</label>
                  <input
                    type="number"
                    step="0.5"
                    value={ingestValue}
                    onChange={(e) => setIngestValue(e.target.value)}
                    className="text-input mono"
                  />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                  Ingest Telemetry Sample
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Right Column: Time-Series Downsampling Studio */}
        <div className="column">
          <div className="card">
            <div className="card-header">
              <h2>📊 Aggregator Downsampling Configuration</h2>
            </div>
            <div className="card-body">
              <div className="controls-grid">
                <div className="form-group">
                  <label>Metric Series</label>
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                    className="text-input"
                  >
                    {metricsList.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Window Size (Resolution)</label>
                  <select
                    value={windowSeconds}
                    onChange={(e) => setWindowSeconds(Number(e.target.value))}
                    className="text-input"
                  >
                    <option value={10}>10 Seconds (High Res)</option>
                    <option value={30}>30 Seconds (Medium Res)</option>
                    <option value={60}>60 Seconds (Standard 1m)</option>
                    <option value={120}>120 Seconds (2m Rollup)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Time Range Start</label>
                  <input
                    type="number"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="text-input mono"
                  />
                </div>

                <div className="form-group">
                  <label>Time Range End</label>
                  <input
                    type="number"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="text-input mono"
                  />
                </div>
              </div>

              <div className="checkbox-wrap">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={fillEmptyWindows}
                    onChange={(e) => setFillEmptyWindows(e.target.checked)}
                  />
                  <span>Fill Empty Windows with Zeroes (Continuous Dashboard Timeline)</span>
                </label>
              </div>
            </div>
          </div>

          {/* Aggregated Buckets Visual Chart */}
          <div className="card">
            <div className="card-header">
              <h2>📈 Time-Window Aggregation Buckets ({buckets.length})</h2>
            </div>
            <div className="card-body">
              <div className="buckets-list">
                {buckets.length === 0 ? (
                  <div className="text-center text-muted" style={{ padding: '2rem' }}>
                    No windows generated for this range.
                  </div>
                ) : (
                  buckets.map((b, idx) => {
                    const isZeroFilled = b.count === 0
                    const barPercent = isZeroFilled ? 0 : Math.min(100, (b.avg / maxAvgInBuckets) * 100)

                    return (
                      <div key={idx} className={`bucket-row ${isZeroFilled ? 'bucket-quiet' : ''}`}>
                        <div className="bucket-info">
                          <div className="bucket-window-title mono">
                            [{b.start_time.toFixed(1)}s - {b.end_time.toFixed(1)}s)
                          </div>
                          {isZeroFilled ? (
                            <span className="badge badge-quiet">QUIET WINDOW (0 SAMPLES)</span>
                          ) : (
                            <span className="badge badge-count">{b.count} samples</span>
                          )}
                        </div>

                        {/* Visual Bar */}
                        <div className="bucket-bar-track">
                          <div
                            className="bucket-bar-fill"
                            style={{ width: `${barPercent}%` }}
                          />
                        </div>

                        {/* Metric stats */}
                        <div className="bucket-stats mono">
                          <span>Avg: <b>{b.avg}</b></span>
                          <span>Min: {b.min}</span>
                          <span>Max: {b.max}</span>
                          <span className="text-cyan">P95: <b>{b.p95}</b></span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

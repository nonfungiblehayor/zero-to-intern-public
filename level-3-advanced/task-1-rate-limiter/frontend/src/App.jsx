import React, { useState, useEffect } from 'react'

export default function App() {
  const [clockTime, setClockTime] = useState(1000.0)
  const [config, setConfig] = useState({ limit: 10, window_seconds: 60.0 })
  const [clients, setClients] = useState({})
  const [selectedClient, setSelectedClient] = useState('client-demo')
  const [endpoint, setEndpoint] = useState('/api/v1/checkout')
  const [burstCount, setBurstCount] = useState(5)
  const [lastResponse, setLastResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

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

  const fetchState = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/state')
      if (!res.ok) throw new Error('Failed to fetch gateway state')
      const data = await res.json()
      setClockTime(data.clock_time)
      setConfig(data.config || { limit: 10, window_seconds: 60.0 })
      setClients(data.clients || {})
      if (!data.clients[selectedClient] && Object.keys(data.clients).length > 0) {
        setSelectedClient(Object.keys(data.clients)[0])
      }
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchState()
  }, [])

  const handleSendRequest = async () => {
    try {
      const res = await fetch('/api/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: selectedClient, endpoint })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')
      setLastResponse(data)
      if (data.status_code === 200) {
        showToast(`200 OK — Remaining: ${data.headers['X-RateLimit-Remaining']}`, 'success')
      } else {
        showToast(`429 Too Many Requests — Retry-After: ${data.headers['Retry-After']}s`, 'error')
      }
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleSendBurst = async () => {
    try {
      const res = await fetch('/api/burst', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: selectedClient, count: burstCount, endpoint })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Burst failed')
      const last = data.results[data.results.length - 1]
      setLastResponse({
        status_code: last.status_code,
        headers: last.headers,
        body: {
          summary: `Burst of ${burstCount}: ${data.allowed} allowed, ${data.blocked} blocked`,
          last_result: last.body
        },
        clock_time: data.clock_time
      })
      showToast(`Burst executed: ${data.allowed} allowed, ${data.blocked} throttled`, data.blocked > 0 ? 'warning' : 'success')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleAdvanceClock = async (seconds) => {
    try {
      const res = await fetch('/api/clock/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seconds: Number(seconds) })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to advance time')
      showToast(`Virtual clock advanced by +${seconds}s (now t=${data.clock_time}s)`, 'info')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleReset = async () => {
    try {
      const res = await fetch('/api/reset', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error('Reset failed')
      setLastResponse(null)
      setScenarioState({ running: false, name: null, logs: [], status: null })
      showToast(`Gateway state and clock reset to t=${data.clock_time}s`, 'info')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  // 1-Click Diagnostics: Ticket #GATE-401 (Sliding Decay Weight Inversion)
  const runScenarioGate401 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #GATE-401: Inverted Sliding Window Decay Weight',
        status: 'running',
        logs: [
          '[1/5] Resetting gateway to clean state...',
          '[2/5] Simulating Client A making 8 requests in Window 1 (t=1000s)...'
        ]
      })

      await fetch('/api/reset', { method: 'POST' })

      // Send 8 requests in window 1
      for (let i = 0; i < 8; i++) {
        await fetch('/api/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ client_id: 'test-sliding-client', endpoint: '/api/resource' })
        })
      }

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Window 1 (t=1000s..1060s): 8 requests stored in client record.',
          '[3/5] Advancing clock by +105.0s (into Window 2, 45s elapsed into 60s window)...'
        ]
      }))

      await fetch('/api/clock/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seconds: 105.0 })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Clock is at t=1105.0s (75% through Window 2).',
          'Mathematical formula expectation:',
          '  time_into_current = 45s, window = 60s -> decay = 1.0 - (45/60) = 0.25 (25% remaining)',
          '  estimated_count = (8 * 0.25) + 0 = 2.0 requests from previous window.',
          '  Capacity remaining = 10 - 2.0 = 8 requests allowed!',
          '[4/5] Sending 8 new requests in Window 2...'
        ]
      }))

      let allowedCount = 0
      for (let i = 0; i < 8; i++) {
        const res = await fetch('/api/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ client_id: 'test-sliding-client', endpoint: '/api/resource' })
        })
        const data = await res.json()
        if (data.status_code === 200) allowedCount++
      }

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Allowed in Window 2: ${allowedCount} of 8 requests.`
        ]
      }))

      if (allowedCount < 7) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Allowed only ${allowedCount} requests (expected >= 7)!`,
            'ROOT CAUSE: Weight formula was inverted (time_into_current / window_seconds = 0.75).',
            'Estimated count was (8 * 0.75) = 6.0 instead of 2.0, throttling valid traffic prematurely!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Allowed ${allowedCount} requests in Window 2.`,
            'SUCCESS: Correct decay weight (1.0 - time_into_current / window_seconds) accurately modeled past traffic.'
          ]
        }))
      }
      await fetchState()
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  // 1-Click Diagnostics: Ticket #GATE-402 (Dormant Counter Resurrection)
  const runScenarioGate402 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #GATE-402: Dormant Counter Resurrection Across Gaps',
        status: 'running',
        logs: [
          '[1/4] Resetting gateway...',
          '[2/4] Saturating client with 10 requests at t=1000s...'
        ]
      })

      await fetch('/api/reset', { method: 'POST' })

      for (let i = 0; i < 10; i++) {
        await fetch('/api/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ client_id: 'test-dormant-client', endpoint: '/api/resource' })
        })
      }

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Client reached 10/10 limit at t=1000s.',
          '[3/4] Advancing clock by 3600.0s (1 hour idle, spanning 60 full windows)...'
        ]
      }))

      await fetch('/api/clock/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seconds: 3600.0 })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Clock is now t=4600s.',
          '[4/4] Sending fresh request after 1 hour idle...'
        ]
      }))

      const res = await fetch('/api/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: 'test-dormant-client', endpoint: '/api/resource' })
      })
      const data = await res.json()

      const statusCode = data.status_code
      const remaining = data.headers['X-RateLimit-Remaining']

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `HTTP Status: ${statusCode}`,
          `X-RateLimit-Remaining: ${remaining}`
        ]
      }))

      if (statusCode === 429 || remaining !== '9') {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Status was ${statusCode} and Remaining was ${remaining}.`,
            'ROOT CAUSE: _sync_window only shifted one window on `elapsed >= window_duration`.',
            'When elapsed >= 2 * window_duration, dormant 10-count was resurrected into previous_window_count!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            '🛡️ PROTECTED! Fresh request allowed with 200 OK and Remaining: 9.',
            'SUCCESS: Multi-window gap properly cleared both current and previous counters.'
          ]
        }))
      }
      await fetchState()
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  // 1-Click Diagnostics: Ticket #GATE-403 (Negative Remaining Header Underflow)
  const runScenarioGate403 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #GATE-403: Negative Remaining Header Underflow',
        status: 'running',
        logs: [
          '[1/3] Resetting gateway...',
          '[2/3] Saturating client with 10 requests at t=1000s...'
        ]
      })

      await fetch('/api/reset', { method: 'POST' })

      for (let i = 0; i < 10; i++) {
        await fetch('/api/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ client_id: 'test-overflow-client', endpoint: '/api/resource' })
        })
      }

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Limit saturated (10/10).',
          '[3/3] Sending 11th request (should be 429 Too Many Requests)...'
        ]
      }))

      const res = await fetch('/api/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: 'test-overflow-client', endpoint: '/api/resource' })
      })
      const data = await res.json()

      const remainingHeader = data.headers['X-RateLimit-Remaining']

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `HTTP Status: ${data.status_code}`,
          `X-RateLimit-Remaining: "${remainingHeader}"`
        ]
      }))

      if (remainingHeader === '-1' || Number(remainingHeader) < 0) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! X-RateLimit-Remaining was "${remainingHeader}" (negative underflow)!`,
            'ROOT CAUSE: On 429, remaining calculation returned `int(limit - estimated_count - 1)` without clamping at 0!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! X-RateLimit-Remaining correctly clamped at "${remainingHeader}".`,
            'SUCCESS: HTTP rate limiting headers comply with standard non-negative integer specs.'
          ]
        }))
      }
      await fetchState()
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

  const activeClientData = clients[selectedClient] || null

  return (
    <div className="app-container">
      {/* Toast Notification */}
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
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <div>
            <div className="brand-title-wrap">
              <h1>CloudGate API Gateway Studio</h1>
              <span className="badge-level">BH-L3-001</span>
              <span className="badge-env">ADVANCED</span>
            </div>
            <p className="brand-subtitle">
              Sliding-Window Rate Limiting Engine • Temporal Decay & Edge Throttling
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn btn-outline" onClick={fetchState} disabled={loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            Refresh
          </button>
          <button className="btn btn-danger-outline" onClick={handleReset}>
            Reset State
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Virtual Clock</div>
          <div className="metric-value text-emerald">
            {clockTime.toFixed(1)}s
          </div>
          <div className="metric-foot">Deterministic TestClock</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Rate Limit Quota</div>
          <div className="metric-value text-cyan">
            {config.limit} <span style={{ fontSize: '1.1rem', color: 'var(--text-muted)' }}>/ {config.window_seconds}s</span>
          </div>
          <div className="metric-foot">Sliding interval duration</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Tracked Clients</div>
          <div className="metric-value text-indigo">
            {Object.keys(clients).length}
          </div>
          <div className="metric-foot">In-memory client buckets</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Active Client Load</div>
          <div className="metric-value text-amber">
            {activeClientData ? activeClientData.estimated_count.toFixed(1) : '0.0'}
          </div>
          <div className="metric-foot">
            {activeClientData ? `${activeClientData.previous_window_count} prev × ${(activeClientData.decay_weight * 100).toFixed(0)}% + ${activeClientData.current_window_count} curr` : 'No active client'}
          </div>
        </div>
      </div>

      {/* Main Grid: Diagnostics & Live Traffic Simulator */}
      <div className="dashboard-grid">
        {/* Left Column: Diagnostics & Virtual Clock */}
        <div className="column">
          {/* 1-Click Defect Reproduction Suite */}
          <div className="card">
            <div className="card-header">
              <h2>⚡ 1-Click Defect Reproduction Suite</h2>
              <span className="card-badge">Edge Diagnostics</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Diagnose subtle edge anomalies in the sliding-window algorithm before and after candidate fixes.
              </p>

              <div className="scenario-buttons">
                <button
                  className="scenario-btn"
                  onClick={runScenarioGate401}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-red"></span>
                    Ticket #GATE-401: Inverted Sliding Weight Decay
                  </div>
                  <div className="scenario-btn-desc">
                    Checks whether past window weight decreases or increases as time advances into the current window.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioGate402}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-amber"></span>
                    Ticket #GATE-402: Dormant Counter Resurrection
                  </div>
                  <div className="scenario-btn-desc">
                    Verifies whether inactive clients for 2+ entire windows properly reset rather than resurrecting old counts.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioGate403}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-cyan"></span>
                    Ticket #GATE-403: Negative Remaining Header Underflow
                  </div>
                  <div className="scenario-btn-desc">
                    Tests if 429 Too Many Requests responses clamp X-RateLimit-Remaining at 0 or output negative integers.
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

          {/* Virtual Time Machine */}
          <div className="card">
            <div className="card-header">
              <h2>⏱️ Virtual Time Machine (Deterministic Time Travel)</h2>
              <span className="card-badge">TestClock</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Advance the server's virtual clock to simulate window rollups, decay intervals, and idle periods without waiting in real time.
              </p>

              <div className="time-buttons-grid">
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(5)}>+5 Seconds</button>
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(15)}>+15 Seconds</button>
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(30)}>+30 Seconds (50% Decay)</button>
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(45)}>+45 Seconds (75% Decay)</button>
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(60)}>+60 Seconds (Full Window)</button>
                <button className="btn btn-outline" onClick={() => handleAdvanceClock(3600)}>+1 Hour (Dormant Gap)</button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Live Gateway Traffic Simulator & Window Visualizer */}
        <div className="column">
          {/* Live Request Simulator */}
          <div className="card">
            <div className="card-header">
              <h2>🚀 Live Gateway Traffic Simulator</h2>
              <span className="card-badge">APIGateway Proxy</span>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label>Target Client ID</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    value={selectedClient}
                    onChange={(e) => setSelectedClient(e.target.value)}
                    className="text-input mono"
                    placeholder="e.g. client-demo"
                  />
                  {Object.keys(clients).length > 0 && (
                    <select
                      value={selectedClient}
                      onChange={(e) => setSelectedClient(e.target.value)}
                      className="text-input"
                      style={{ width: '160px' }}
                    >
                      {Object.keys(clients).map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label>Target API Endpoint</label>
                <input
                  type="text"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  className="text-input mono"
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button className="btn btn-primary" onClick={handleSendRequest} style={{ flex: 1 }}>
                  Send Single Request
                </button>
                <div style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={burstCount}
                    onChange={(e) => setBurstCount(Number(e.target.value))}
                    className="text-input mono"
                    style={{ width: '70px', textAlign: 'center' }}
                  />
                  <button className="btn btn-outline" onClick={handleSendBurst} style={{ flex: 1 }}>
                    Send Burst
                  </button>
                </div>
              </div>

              {/* Response Preview */}
              {lastResponse && (
                <div className="response-box">
                  <div className="response-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span className={`status-pill ${lastResponse.status_code === 200 ? 'status-pill-ok' : 'status-pill-err'}`}>
                        {lastResponse.status_code} {lastResponse.status_code === 200 ? 'OK' : 'TOO MANY REQUESTS'}
                      </span>
                      <span className="mono text-muted" style={{ fontSize: '0.75rem' }}>
                        at t={lastResponse.clock_time}s
                      </span>
                    </div>
                  </div>

                  <div className="headers-box">
                    <div className="header-item">
                      <span className="header-key">X-RateLimit-Limit:</span>
                      <span className="header-val">{lastResponse.headers['X-RateLimit-Limit']}</span>
                    </div>
                    <div className="header-item">
                      <span className="header-key">X-RateLimit-Remaining:</span>
                      <span className={`header-val ${Number(lastResponse.headers['X-RateLimit-Remaining']) < 0 ? 'text-red' : 'text-emerald'}`}>
                        {lastResponse.headers['X-RateLimit-Remaining']}
                      </span>
                    </div>
                    <div className="header-item">
                      <span className="header-key">X-RateLimit-Reset:</span>
                      <span className="header-val">{lastResponse.headers['X-RateLimit-Reset']}s</span>
                    </div>
                    {lastResponse.headers['Retry-After'] && (
                      <div className="header-item">
                        <span className="header-key text-red">Retry-After:</span>
                        <span className="header-val text-red">{lastResponse.headers['Retry-After']}s</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sliding Window Visualizer */}
          <div className="card">
            <div className="card-header">
              <h2>📊 Sliding-Window Counter Anatomy</h2>
              <span className="card-badge">{selectedClient}</span>
            </div>
            <div className="card-body">
              {activeClientData ? (
                <div>
                  <div className="window-stats-grid">
                    <div className="window-stat">
                      <span className="stat-label">Previous Window</span>
                      <span className="stat-value">{activeClientData.previous_window_count} reqs</span>
                    </div>
                    <div className="window-stat">
                      <span className="stat-label">Current Window</span>
                      <span className="stat-value">{activeClientData.current_window_count} reqs</span>
                    </div>
                    <div className="window-stat">
                      <span className="stat-label">Elapsed into Window</span>
                      <span className="stat-value">{activeClientData.time_into_current.toFixed(1)}s / {config.window_seconds}s</span>
                    </div>
                    <div className="window-stat">
                      <span className="stat-label">Decay Weight</span>
                      <span className="stat-value text-cyan">{(activeClientData.decay_weight * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {/* Capacity Bar */}
                  <div style={{ marginTop: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.4rem' }}>
                      <span className="text-muted">Estimated Capacity Used: <b>{activeClientData.estimated_count.toFixed(1)} / {config.limit}</b></span>
                      <span className={activeClientData.estimated_count >= config.limit ? 'text-red' : 'text-emerald'}>
                        {activeClientData.estimated_count >= config.limit ? 'LIMIT SATURATED' : `${(config.limit - activeClientData.estimated_count).toFixed(1)} AVAILABLE`}
                      </span>
                    </div>
                    <div className="capacity-bar-track">
                      <div
                        className={`capacity-bar-fill ${activeClientData.estimated_count >= config.limit ? 'fill-red' : 'fill-emerald'}`}
                        style={{ width: `${Math.min(100, (activeClientData.estimated_count / config.limit) * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="formula-box mono">
                    <div><b>Sliding-Window Estimate Formula:</b></div>
                    <div style={{ color: 'var(--cyan)', marginTop: '0.25rem' }}>
                      estimated = (prev_count × decay_weight) + curr_count
                    </div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '0.25rem', fontSize: '0.78rem' }}>
                      = ({activeClientData.previous_window_count} × {activeClientData.decay_weight.toFixed(2)}) + {activeClientData.current_window_count} = <b>{activeClientData.estimated_count.toFixed(1)}</b>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted" style={{ padding: '2rem' }}>
                  No active rate limit bucket for <b>{selectedClient}</b>. Send a request to initiate tracking.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

import React, { useState, useEffect } from 'react'

export default function App() {
  const [endpoints, setEndpoints] = useState([])
  const [deliveries, setDeliveries] = useState([])
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  // Dispatcher form
  const [selectedEndpoint, setSelectedEndpoint] = useState('')
  const [eventType, setEventType] = useState('payment.completed')
  const [payloadStr, setPayloadStr] = useState(JSON.stringify({
    order_id: 'ord_9872',
    amount: 149.50,
    currency: 'USD',
    customer: { id: 'cust_42', email: 'sam@eventbridge.io' }
  }, null, 2))
  const [mockStatusCode, setMockStatusCode] = useState(200)

  // Last dispatch result
  const [dispatchResult, setDispatchResult] = useState(null)

  // 1-Click Diagnostic Suite
  const [scenarioState, setScenarioState] = useState({
    running: false,
    name: null,
    logs: [],
    status: null // 'vulnerable' | 'fixed' | 'error'
  })

  // Signature Verifier Tool
  const [verifySecret, setVerifySecret] = useState('whsec_test_secret_abc123')
  const [verifySigHeader, setVerifySigHeader] = useState('')
  const [verifyPayload, setVerifyPayload] = useState('{"amount":149.5,"order_id":"ord_9872"}')
  const [verifyResult, setVerifyResult] = useState(null)

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const fetchState = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/state')
      if (!res.ok) throw new Error('Failed to load webhook dispatcher state')
      const data = await res.json()
      setEndpoints(data.endpoints || [])
      setDeliveries(data.deliveries || [])
      if (!selectedEndpoint && data.endpoints?.length > 0) {
        setSelectedEndpoint(data.endpoints[0].endpoint_id)
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

  const handleDispatch = async (e) => {
    if (e) e.preventDefault()
    let parsedPayload
    try {
      parsedPayload = JSON.parse(payloadStr)
    } catch (err) {
      showToast('Invalid JSON in payload editor', 'error')
      return
    }

    try {
      const res = await fetch('/api/webhooks/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint_id: selectedEndpoint,
          event_type: eventType,
          payload: parsedPayload,
          mock_status_code: mockStatusCode === 0 ? null : Number(mockStatusCode),
          mock_error: mockStatusCode >= 400 || mockStatusCode === 0 ? `Simulated HTTP status ${mockStatusCode}` : null
        })
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Dispatch failed')

      setDispatchResult(data)
      setVerifySigHeader(data.signature_header)
      setVerifyPayload(JSON.stringify(parsedPayload))
      showToast(`Webhook dispatched: ${data.delivery.status}`, 'success')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleVerifySignature = async () => {
    let parsed
    try {
      parsed = JSON.parse(verifyPayload)
    } catch (err) {
      showToast('Invalid JSON in verification payload', 'error')
      return
    }

    try {
      const res = await fetch('/api/webhooks/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          secret: verifySecret,
          signature_header: verifySigHeader,
          payload: parsed
        })
      })
      const data = await res.json()
      setVerifyResult(data.is_valid)
      if (data.is_valid) {
        showToast('HMAC Signature Authenticated (MATCH)', 'success')
      } else {
        showToast('Signature Verification FAILED (MISMATCH)', 'error')
      }
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleReset = async () => {
    try {
      await fetch('/api/reset', { method: 'POST' })
      showToast('EventBridge state reset to default demo', 'info')
      setDispatchResult(null)
      setVerifyResult(null)
      setScenarioState({ running: false, name: null, logs: [], status: null })
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  // 1-Click Diagnostics
  const runScenarioHook401 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #HOOK-401: HMAC Canonical JSON Formatting',
      logs: ['[INIT] Testing HMAC generation and receiver verification...'],
      status: null
    })

    try {
      const testSecret = 'whsec_prod_key_999'
      const testPayload = { foo: 'bar', z: 1, a: 2 }

      // Dispatch event to partner
      const res = await fetch('/api/webhooks/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint_id: endpoints[0]?.endpoint_id || 'ep_stripe_billing',
          event_type: 'test.signature',
          payload: testPayload,
          mock_status_code: 200
        })
      })
      const data = await res.json()
      const sigHeader = data.signature_header

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ Event dispatched: ${data.event_id}`,
          `✓ Signature Header generated: ${sigHeader.slice(0, 32)}...`,
          `[VERIFICATION] Consumer receiver validates HMAC against standard JSON bytes...`
        ]
      }))

      // Verify on consumer side
      const verifyRes = await fetch('/api/webhooks/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          secret: endpoints[0]?.secret || 'whsec_test_secret_abc123',
          signature_header: sigHeader,
          payload: testPayload
        })
      })
      const verifyData = await verifyRes.json()

      if (!verifyData.is_valid) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Signature Verification FAILED!`,
            `ROOT CAUSE: WebhookSigner serialized Python dict directly using str(payload) with single quotes instead of deterministic canonical JSON with sorted keys and compact separators!`
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Signature successfully verified against canonical JSON bytes!`,
            `SUCCESS: Canonical formatting confirmed.`
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

  const runScenarioHook402 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #HOOK-402: Client 4xx Error Non-Retry Policy',
      logs: ['[INIT] Simulating HTTP 401 Unauthorized response from downstream receiver...'],
      status: null
    })

    try {
      const res = await fetch('/api/webhooks/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint_id: endpoints[0]?.endpoint_id || 'ep_stripe_billing',
          event_type: 'invoice.failed',
          payload: { invoice_id: 'inv_401' },
          mock_status_code: 401,
          mock_error: 'Unauthorized destination endpoint'
        })
      })
      const data = await res.json()
      const status = data.delivery.status

      if (status === 'RETRYING') {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Status is RETRYING (Next retry at ${data.delivery.next_retry_at})`,
            `ROOT CAUSE: RetryPolicy treated 401 Unauthorized as retryable! Client 4xx errors are permanent and must fail immediately without spamming receiver.`
          ]
        }))
      } else if (status === 'FAILED') {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Delivery transitioned immediately to FAILED without scheduling retries.`,
            `SUCCESS: 4xx non-retryable status discrimination verified.`
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

  const runScenarioHook403 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #HOOK-403: Exponential Backoff Progression',
      logs: ['[INIT] Querying retry policy backoff progression for attempts 1, 2, 3, 4 (initial=1.0s, factor=2.0)...'],
      status: null
    })

    try {
      const res = await fetch('/api/backoff/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_attempts: 4, initial_delay: 1.0, backoff_factor: 2.0 })
      })
      const data = await res.json()
      const delays = data.delays

      const isLinearDefect = delays.every(d => d === 2.0)
      const isExponential = delays[0] === 1.0 && delays[1] === 2.0 && delays[2] === 4.0 && delays[3] === 8.0

      if (isLinearDefect) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `Delays computed: [${delays.join(', ')}]`,
            `🚨 VULNERABILITY DETECTED! Fixed 2.0s delay returned for all attempts!`,
            `ROOT CAUSE: RetryPolicy.compute_next_delay() multiplies initial_delay * backoff_factor linearly instead of raising to the (attempt - 1) power!`
          ]
        }))
      } else if (isExponential) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `Delays computed: [${delays.join('s, ')}s]`,
            `🛡️ PROTECTED! Progression is mathematically geometric: 1.0s -> 2.0s -> 4.0s -> 8.0s.`,
            `SUCCESS: Correct exponential backoff formula confirmed.`
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `Delays computed: [${delays.join(', ')}]`,
            `Expected [1.0, 2.0, 4.0, 8.0]. Formula still requires correction.`
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

  const deliveredCount = deliveries.filter(d => d.status === 'DELIVERED').length
  const retryingCount = deliveries.filter(d => d.status === 'RETRYING').length
  const failedCount = deliveries.filter(d => d.status === 'FAILED').length

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
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div>
            <div className="brand-title-wrap">
              <h1>EventBridge Webhook Studio</h1>
              <span className="badge-level">BH-L2-004</span>
              <span className="badge-env">INTERMEDIATE</span>
            </div>
            <p className="brand-subtitle">
              High-Reliability Event Delivery • HMAC Signing & Exponential Backoff Engine
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
            Reset Queue
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Registered Endpoints</div>
          <div className="metric-value text-indigo">{endpoints.length}</div>
          <div className="metric-foot">Target customer destinations</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Delivered (2xx)</div>
          <div className="metric-value text-emerald">{deliveredCount}</div>
          <div className="metric-foot">Successfully acknowledged</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Retrying Queue</div>
          <div className="metric-value text-amber">{retryingCount}</div>
          <div className="metric-foot">Backoff scheduled</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Failed Deliveries</div>
          <div className="metric-value text-red">{failedCount}</div>
          <div className="metric-foot">Permanent 4xx / Max retry</div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Defect Reproduction Scenarios */}
        <div className="column">
          <div className="card">
            <div className="card-header">
              <h2>⚡ 1-Click Defect Reproduction Suite</h2>
              <span className="card-badge">Vulnerability Diagnostics</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Diagnose known defects across HMAC canonical signing, 4xx retry storms, and backoff scaling.
              </p>

              <div className="scenario-buttons">
                <button
                  className="scenario-btn"
                  onClick={runScenarioHook401}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-red"></span>
                    Ticket #HOOK-401: HMAC Canonical Formatting
                  </div>
                  <div className="scenario-btn-desc">
                    Generates an event signature and verifies whether consumer receivers reject it due to non-canonical string formatting.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioHook402}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-amber"></span>
                    Ticket #HOOK-402: 4xx Client Error Retry Storm
                  </div>
                  <div className="scenario-btn-desc">
                    Simulates 401 Unauthorized response to check if dispatcher erroneously schedules infinite retries.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioHook403}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-violet"></span>
                    Ticket #HOOK-403: Exponential Backoff Scaling
                  </div>
                  <div className="scenario-btn-desc">
                    Evaluates mathematical backoff progression for attempts 1..4 (expected: 1s, 2s, 4s, 8s).
                  </div>
                </button>
              </div>

              {/* Scenario Terminal Output */}
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

          {/* HMAC Signature Verifier */}
          <div className="card">
            <div className="card-header">
              <h2>🔒 HMAC-SHA256 Signature Verifier</h2>
              <span className="card-badge">Consumer Side</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Verify webhook authenticity as an external consumer receiving our HTTP payload.
              </p>

              <div className="form-group">
                <label>Webhook Secret Key</label>
                <input
                  type="text"
                  value={verifySecret}
                  onChange={(e) => setVerifySecret(e.target.value)}
                  className="text-input mono"
                />
              </div>

              <div className="form-group">
                <label>Signature Header (X-EventBridge-Signature)</label>
                <input
                  type="text"
                  placeholder="t=...,v1=..."
                  value={verifySigHeader}
                  onChange={(e) => setVerifySigHeader(e.target.value)}
                  className="text-input mono"
                />
              </div>

              <div className="form-group">
                <label>Received JSON Body</label>
                <textarea
                  rows="3"
                  value={verifyPayload}
                  onChange={(e) => setVerifyPayload(e.target.value)}
                  className="text-input mono"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button className="btn btn-primary" onClick={handleVerifySignature}>
                  Verify Signature Match
                </button>
                {verifyResult !== null && (
                  <span className={`badge ${verifyResult ? 'badge-active' : 'badge-revoked'}`}>
                    {verifyResult ? 'VALID MATCH' : 'INVALID SIGNATURE'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Live Webhook Dispatcher */}
        <div className="column">
          <div className="card">
            <div className="card-header">
              <h2>🚀 Live Webhook Event Dispatcher</h2>
              <span className="card-badge">POST /api/webhooks/dispatch</span>
            </div>
            <div className="card-body">
              <form onSubmit={handleDispatch}>
                <div className="form-group">
                  <label>Destination Endpoint</label>
                  <select
                    value={selectedEndpoint}
                    onChange={(e) => setSelectedEndpoint(e.target.value)}
                    className="text-input"
                  >
                    {endpoints.map((ep) => (
                      <option key={ep.endpoint_id} value={ep.endpoint_id}>
                        {ep.endpoint_id} ({ep.url})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Event Type</label>
                  <input
                    type="text"
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value)}
                    className="text-input mono"
                  />
                </div>

                <div className="form-group">
                  <label>Simulated Destination Response</label>
                  <select
                    value={mockStatusCode}
                    onChange={(e) => setMockStatusCode(e.target.value)}
                    className="text-input"
                  >
                    <option value={200}>200 OK (Successful Delivery)</option>
                    <option value={500}>500 Internal Server Error (Retryable)</option>
                    <option value={503}>503 Service Unavailable (Retryable)</option>
                    <option value={0}>Network Timeout / Connection Dropped (Retryable)</option>
                    <option value={401}>401 Unauthorized (Client Error — Non-Retryable)</option>
                    <option value={404}>404 Not Found (Client Error — Non-Retryable)</option>
                    <option value={422}>422 Unprocessable Entity (Client Error — Non-Retryable)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>JSON Payload Editor</label>
                  <textarea
                    rows="5"
                    value={payloadStr}
                    onChange={(e) => setPayloadStr(e.target.value)}
                    className="text-input mono"
                  />
                </div>

                <button type="submit" className="btn btn-success" style={{ width: '100%' }}>
                  Dispatch Webhook Event
                </button>
              </form>

              {/* Dispatch Result Card */}
              {dispatchResult && (
                <div className={`vault-result ${dispatchResult.delivery.status === 'DELIVERED' ? 'vault-granted' : 'vault-denied'}`}>
                  <div className="vault-status-bar">
                    <span className="vault-badge">
                      STATUS: {dispatchResult.delivery.status} (Attempts: {dispatchResult.delivery.attempts.length})
                    </span>
                    <span className="mono">{dispatchResult.event_id}</span>
                  </div>
                  <pre className="vault-json mono">
                    {JSON.stringify(dispatchResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Deliveries Queue Table */}
      <div className="tables-section">
        <div className="card">
          <div className="card-header">
            <h2>Webhook Delivery History & Retry Queue ({deliveries.length})</h2>
          </div>
          <div className="card-body p-0">
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Event ID</th>
                    <th>Target Endpoint</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Last Status Code</th>
                    <th>Next Retry In</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center text-muted">No webhook deliveries dispatched yet.</td>
                    </tr>
                  ) : (
                    deliveries.map((del) => {
                      const lastAttempt = del.attempts[del.attempts.length - 1]
                      return (
                        <tr key={del.event_id}>
                          <td className="mono font-semibold">{del.event_id}</td>
                          <td className="mono text-sm">{del.endpoint_id}</td>
                          <td>
                            <span className={`badge ${
                              del.status === 'DELIVERED' ? 'badge-active' :
                              del.status === 'RETRYING' ? 'badge-used' : 'badge-revoked'
                            }`}>
                              {del.status}
                            </span>
                          </td>
                          <td className="mono text-center">{del.attempts.length}</td>
                          <td className="mono">
                            {lastAttempt?.status_code ? (
                              <span className={lastAttempt.status_code === 200 ? 'text-emerald' : 'text-red'}>
                                {lastAttempt.status_code}
                              </span>
                            ) : (
                              <span className="text-amber">TIMEOUT</span>
                            )}
                          </td>
                          <td className="mono text-muted text-sm">
                            {del.next_retry_at ? `+${(del.next_retry_at - (lastAttempt?.timestamp || 0)).toFixed(1)}s` : '—'}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

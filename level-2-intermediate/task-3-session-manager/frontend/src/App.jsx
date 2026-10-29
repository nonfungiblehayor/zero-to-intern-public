import React, { useState, useEffect } from 'react'

export default function App() {
  const [sessions, setSessions] = useState([])
  const [tokens, setTokens] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)

  // Form states
  const [userIdInput, setUserIdInput] = useState('')
  const [testTokenId, setTestTokenId] = useState('')
  const [testRefreshId, setTestRefreshId] = useState('')

  // Verification results
  const [vaultResult, setVaultResult] = useState(null)
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
      if (!res.ok) throw new Error('Failed to load security state')
      const data = await res.json()
      setSessions(data.sessions || [])
      setTokens(data.tokens || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchState()
  }, [])

  // Auto-select latest tokens for quick testing
  useEffect(() => {
    if (!testTokenId && tokens.length > 0) {
      const accessTokens = tokens.filter(t => t.token_type === 'ACCESS')
      if (accessTokens.length > 0) {
        setTestTokenId(accessTokens[accessTokens.length - 1].token_id)
      }
    }
    if (!testRefreshId && tokens.length > 0) {
      const refreshTokens = tokens.filter(t => t.token_type === 'REFRESH')
      if (refreshTokens.length > 0) {
        setTestRefreshId(refreshTokens[refreshTokens.length - 1].token_id)
      }
    }
  }, [tokens])

  const handleCreateSession = async (e) => {
    if (e) e.preventDefault()
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userIdInput })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to create session')

      showToast(`Session issued for ${userIdInput || '[empty]'}`, 'success')
      setUserIdInput('')
      setTestTokenId(data.access_token.token_id)
      setTestRefreshId(data.refresh_token.token_id)
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleRevokeSession = async (sessionId) => {
    try {
      const res = await fetch(`/api/sessions/${sessionId}/revoke`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to revoke session')
      showToast(`Session ${sessionId.slice(0, 10)}... revoked`, 'warning')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleRevokeAllUser = async (userId) => {
    try {
      const res = await fetch('/api/sessions/revoke-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to revoke user sessions')
      showToast(`Revoked ${data.revoked_count} sessions for ${userId}`, 'warning')
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleTestProtectedVault = async () => {
    if (!testTokenId) {
      showToast('Please select or input an access token', 'error')
      return
    }
    try {
      setVaultResult(null)
      const res = await fetch('/api/protected', {
        headers: {
          'Authorization': `Bearer ${testTokenId.trim()}`
        }
      })
      const data = await res.json()
      setVaultResult({
        status: res.status,
        ok: res.ok,
        data
      })
      if (res.ok) {
        showToast('Vault Clearance Granted (200 OK)', 'success')
      } else {
        showToast(`Access Denied (${res.status}): ${data.detail || 'Unauthorized'}`, 'error')
      }
    } catch (err) {
      setVaultResult({
        status: 500,
        ok: false,
        data: { detail: err.message }
      })
    }
  }

  const handleRotateRefreshToken = async () => {
    if (!testRefreshId) {
      showToast('Please select or input a refresh token', 'error')
      return
    }
    try {
      const res = await fetch('/api/tokens/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token_id: testRefreshId.trim() })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Token refresh failed')

      showToast('Token pair rotated successfully', 'success')
      setTestTokenId(data.access_token.token_id)
      setTestRefreshId(data.refresh_token.token_id)
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleReset = async () => {
    try {
      await fetch('/api/reset', { method: 'POST' })
      showToast('Security registry reset to factory demo state', 'info')
      setVaultResult(null)
      setScenarioState({ running: false, name: null, logs: [], status: null })
      await fetchState()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  // Automated 1-Click Bug Reproduction Scenarios
  const runScenarioAuth301 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #AUTH-301: Session Revocation Bypass',
      logs: ['[INIT] Creating ephemeral test session for victim_user@authshield.io...'],
      status: null
    })

    try {
      // 1. Create session
      const createRes = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'victim_user@authshield.io' })
      })
      const createData = await createRes.json()
      const sessId = createData.session.session_id
      const accId = createData.access_token.token_id

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ Session created: ${sessId}`,
          `✓ Access token issued: ${accId.slice(0, 16)}...`,
          `[ACTION] User logs out -> Revoking session ${sessId}...`
        ]
      }))

      // 2. Revoke session
      await fetch(`/api/sessions/${sessId}/revoke`, { method: 'POST' })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ Session marked as REVOKED in SessionStore.`,
          `[TEST] Calling GET /api/protected with previous Access Token...`
        ]
      }))

      // 3. Test protected endpoint
      const protRes = await fetch('/api/protected', {
        headers: { 'Authorization': `Bearer ${accId}` }
      })
      const protData = await protRes.json()

      if (protRes.status === 200) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Response: 200 OK`,
            `Payload: ${JSON.stringify(protData)}`,
            `ROOT CAUSE: AuthMiddleware / TokenService validated expiration locally but failed to check if Session ${sessId} is revoked!`
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Response: ${protRes.status} ${protData.detail || 'Unauthorized'}`,
            `SUCCESS: Token correctly rejected because underlying session is revoked.`
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

  const runScenarioAuth302 = async () => {
    setScenarioState({
      running: true,
      name: 'Ticket #AUTH-302: Refresh Token Reuse (Replay Attack)',
      logs: ['[INIT] Creating session & initial tokens for replay test...'],
      status: null
    })

    try {
      // 1. Create session
      const createRes = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'replay_attacker@authshield.io' })
      })
      const createData = await createRes.json()
      const refId = createData.refresh_token.token_id

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ Refresh token issued: ${refId.slice(0, 18)}...`,
          `[ACTION 1] Legitimate client rotates refresh token once...`
        ]
      }))

      // 2. Rotate once (legitimate)
      const ref1Res = await fetch('/api/tokens/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token_id: refId })
      })
      const ref1Data = await ref1Res.json()

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `✓ First rotation succeeded: New access token generated.`,
          `[ACTION 2] Attacker attempts REPLAY of original refresh token ${refId.slice(0, 18)}...`
        ]
      }))

      // 3. Rotate second time with SAME old token (attacker replay)
      const ref2Res = await fetch('/api/tokens/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token_id: refId })
      })
      const ref2Data = await ref2Res.json()

      if (ref2Res.status === 200) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            `🚨 VULNERABILITY DETECTED! Second refresh succeeded with 200 OK!`,
            `ROOT CAUSE: Refresh tokens are NOT single-use! Old tokens are never marked as used, allowing infinite token minting.`
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            `🛡️ PROTECTED! Second refresh rejected (${ref2Res.status}): ${ref2Data.detail || 'Token already used'}`,
            `SUCCESS: Single-use token rotation verified. Replayed refresh token blocked!`
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

  // Active counts
  const activeSessionsCount = sessions.filter(s => !s.is_revoked).length
  const revokedSessionsCount = sessions.filter(s => s.is_revoked).length
  const accessTokensCount = tokens.filter(t => t.token_type === 'ACCESS').length
  const refreshTokensCount = tokens.filter(t => t.token_type === 'REFRESH').length

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

      {/* Top Header */}
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
              <h1>AuthShield SOC Console</h1>
              <span className="badge-level">BH-L2-003</span>
              <span className="badge-env">INTERMEDIATE</span>
            </div>
            <p className="brand-subtitle">
              Security Operations Center • Central Session Registry & Token Rotation Engine
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn btn-outline" onClick={fetchState} disabled={loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            Refresh State
          </button>
          <button className="btn btn-danger-outline" onClick={handleReset}>
            Reset Registry
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Active Sessions</div>
          <div className="metric-value text-emerald">{activeSessionsCount}</div>
          <div className="metric-foot">Currently authenticated</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Revoked Sessions</div>
          <div className="metric-value text-amber">{revokedSessionsCount}</div>
          <div className="metric-foot">Logged out / Terminated</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Access Tokens</div>
          <div className="metric-value text-cyan">{accessTokensCount}</div>
          <div className="metric-foot">Short-lived credentials</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Refresh Tokens</div>
          <div className="metric-value text-violet">{refreshTokensCount}</div>
          <div className="metric-foot">Long-lived rotation keys</div>
        </div>
      </div>

      {/* Main Grid: Playground & Inspector */}
      <div className="dashboard-grid">
        {/* Left Column: Defect Reproduction Scenarios & Token Generator */}
        <div className="column">
          {/* Automated Defect Reproduction */}
          <div className="card">
            <div className="card-header">
              <h2>⚡ 1-Click Defect Reproduction Suite</h2>
              <span className="card-badge">SOC Reproducers</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Execute automated diagnostic flows to verify whether known architectural vulnerabilities exist in this build.
              </p>

              <div className="scenario-buttons">
                <button
                  className="scenario-btn"
                  onClick={runScenarioAuth301}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-red"></span>
                    Ticket #AUTH-301: Session Revocation Bypass
                  </div>
                  <div className="scenario-btn-desc">
                    Revokes a session and verifies whether active access tokens are immediately rejected.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioAuth302}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-amber"></span>
                    Ticket #AUTH-302: Single-Use Rotation Replay
                  </div>
                  <div className="scenario-btn-desc">
                    Rotates a refresh token and attempts to replay the spent token a second time.
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

          {/* Issue New Session */}
          <div className="card">
            <div className="card-header">
              <h2>🔑 Issue New Session & Credentials</h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleCreateSession} className="session-form">
                <div className="form-group">
                  <label>Target User ID or Email</label>
                  <div className="input-row">
                    <input
                      type="text"
                      placeholder="e.g. charlie@authshield.io (or leave empty to test validation)"
                      value={userIdInput}
                      onChange={(e) => setUserIdInput(e.target.value)}
                      className="text-input"
                    />
                    <button type="submit" className="btn btn-primary">
                      Create Session
                    </button>
                  </div>
                  <span className="input-hint">
                    Note: Creating a session with an empty string should be rejected with ValueError.
                  </span>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Right Column: Protected Endpoint Vault & Token Rotation */}
        <div className="column">
          {/* Protected Endpoint Vault Clearance */}
          <div className="card">
            <div className="card-header">
              <h2>🛡️ Protected Security Vault clearance</h2>
              <span className="card-badge">GET /api/protected</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Simulate an authenticated HTTP request intercepted by <code>AuthMiddleware</code>.
              </p>

              <div className="form-group">
                <label>Access Token (Bearer Header)</label>
                <div className="input-row">
                  <input
                    type="text"
                    value={testTokenId}
                    onChange={(e) => setTestTokenId(e.target.value)}
                    placeholder="acc_..."
                    className="text-input mono"
                  />
                  <button
                    className="btn btn-success"
                    onClick={handleTestProtectedVault}
                  >
                    Send Request
                  </button>
                </div>
              </div>

              {/* Live Request Preview */}
              <div className="request-preview">
                <div className="preview-label">HTTP Header Preview:</div>
                <div className="preview-code mono">
                  Authorization: Bearer {testTokenId || '&lt;TOKEN_ID&gt;'}
                </div>
              </div>

              {/* Vault Result */}
              {vaultResult && (
                <div className={`vault-result ${vaultResult.ok ? 'vault-granted' : 'vault-denied'}`}>
                  <div className="vault-status-bar">
                    <span className="vault-badge">
                      {vaultResult.ok ? '✓ 200 OK — ACCESS GRANTED' : `✕ ${vaultResult.status} — ACCESS DENIED`}
                    </span>
                    <span className="mono">{vaultResult.ok ? 'CLEARANCE LEVEL 1' : 'SECURITY BREACH PREVENTED'}</span>
                  </div>
                  <pre className="vault-json mono">
                    {JSON.stringify(vaultResult.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>

          {/* Token Rotation Engine */}
          <div className="card">
            <div className="card-header">
              <h2>🔄 Single-Use Refresh Token Rotation</h2>
              <span className="card-badge">POST /api/tokens/refresh</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Execute refresh token exchange. In a secure implementation, the submitted refresh token must be permanently invalidated immediately upon exchange.
              </p>

              <div className="form-group">
                <label>Refresh Token ID</label>
                <div className="input-row">
                  <input
                    type="text"
                    value={testRefreshId}
                    onChange={(e) => setTestRefreshId(e.target.value)}
                    placeholder="ref_..."
                    className="text-input mono"
                  />
                  <button
                    className="btn btn-primary"
                    onClick={handleRotateRefreshToken}
                  >
                    Rotate Token
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* State Tables: Sessions & Tokens */}
      <div className="tables-section">
        {/* Sessions Registry */}
        <div className="card">
          <div className="card-header">
            <h2>Active & Historical Sessions Registry ({sessions.length})</h2>
          </div>
          <div className="card-body p-0">
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Session ID</th>
                    <th>User ID</th>
                    <th>Created</th>
                    <th>Expires</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center text-muted">No sessions in registry.</td>
                    </tr>
                  ) : (
                    sessions.map((sess) => (
                      <tr key={sess.session_id} className={sess.is_revoked ? 'row-revoked' : ''}>
                        <td className="mono font-semibold">{sess.session_id}</td>
                        <td>{sess.user_id}</td>
                        <td className="text-muted text-sm">{sess.created_at.slice(11, 19)}</td>
                        <td className="text-muted text-sm">{sess.expires_at.slice(0, 10)}</td>
                        <td>
                          {sess.is_revoked ? (
                            <span className="badge badge-revoked">REVOKED</span>
                          ) : (
                            <span className="badge badge-active">ACTIVE</span>
                          )}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {!sess.is_revoked && (
                            <div className="action-btn-group">
                              <button
                                className="btn-table btn-table-danger"
                                onClick={() => handleRevokeSession(sess.session_id)}
                              >
                                Revoke
                              </button>
                              <button
                                className="btn-table btn-table-warn"
                                onClick={() => handleRevokeAllUser(sess.user_id)}
                                title="Revoke all sessions for this user"
                              >
                                Revoke All
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Tokens Registry */}
        <div className="card mt-6">
          <div className="card-header">
            <h2>Cryptographic Tokens Registry ({tokens.length})</h2>
          </div>
          <div className="card-body p-0">
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Token ID</th>
                    <th>Type</th>
                    <th>User / Session</th>
                    <th>Expires</th>
                    <th>Flags</th>
                    <th style={{ textAlign: 'right' }}>Quick Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tokens.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center text-muted">No tokens in registry.</td>
                    </tr>
                  ) : (
                    tokens.map((tok) => {
                      const parentSession = sessions.find(s => s.session_id === tok.session_id)
                      const isRevokedBySession = parentSession?.is_revoked

                      return (
                        <tr key={tok.token_id}>
                          <td className="mono text-sm">{tok.token_id}</td>
                          <td>
                            <span className={`badge ${tok.token_type === 'ACCESS' ? 'badge-cyan' : 'badge-violet'}`}>
                              {tok.token_type}
                            </span>
                          </td>
                          <td className="text-sm">
                            <div>{tok.user_id}</div>
                            <div className="text-muted mono text-xs">{tok.session_id}</div>
                          </td>
                          <td className="text-muted text-sm">{tok.expires_at.slice(11, 19)}</td>
                          <td>
                            {tok.is_used && <span className="badge badge-used">USED</span>}
                            {isRevokedBySession && <span className="badge badge-revoked">SESSION REVOKED</span>}
                            {!tok.is_used && !isRevokedBySession && <span className="badge badge-active">VALID</span>}
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            {tok.token_type === 'ACCESS' ? (
                              <button
                                className="btn-table btn-table-primary"
                                onClick={() => {
                                  setTestTokenId(tok.token_id)
                                  showToast('Loaded into Vault Clearance tester', 'info')
                                }}
                              >
                                Test Access
                              </button>
                            ) : (
                              <button
                                className="btn-table btn-table-primary"
                                onClick={() => {
                                  setTestRefreshId(tok.token_id)
                                  showToast('Loaded into Token Rotation tester', 'info')
                                }}
                              >
                                Test Rotate
                              </button>
                            )}
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

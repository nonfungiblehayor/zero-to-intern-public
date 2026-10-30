import React, { useState, useEffect } from 'react'

export default function App() {
  const [tasks, setTasks] = useState([])
  const [hasCycle, setHasCycle] = useState(false)
  const [lastRunResult, setLastRunResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  // Add task form
  const [newTaskId, setNewTaskId] = useState('')
  const [newDependencies, setNewDependencies] = useState('')
  const [newShouldFail, setNewShouldFail] = useState(false)
  const [newFailMessage, setNewFailMessage] = useState('Service timeout 504')

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

  const fetchWorkflow = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/workflow')
      if (!res.ok) throw new Error('Failed to fetch workflow')
      const data = await res.json()
      setTasks(data.tasks || [])
      setHasCycle(data.has_cycle || false)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkflow()
  }, [])

  const handleRunWorkflow = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/workflow/run', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Workflow execution failed')
      setLastRunResult(data)
      setHasCycle(data.has_cycle || false)
      if (data.tasks) setTasks(data.tasks)

      if (data.has_cycle) {
        showToast('Execution aborted: Directed cycle detected in graph!', 'error')
      } else if (data.is_successful) {
        showToast(`Workflow execution finished: All ${data.completed_tasks.length} tasks completed`, 'success')
      } else {
        showToast(`Workflow failed: ${data.failed_tasks.length} failed, ${data.skipped_tasks.length} skipped`, 'error')
      }
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyTemplate = async (template) => {
    try {
      const res = await fetch('/api/workflow/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template })
      })
      if (!res.ok) throw new Error('Failed to apply template')
      setLastRunResult(null)
      showToast(`Applied template: "${template}"`, 'info')
      await fetchWorkflow()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleResetWorkflow = async () => {
    try {
      await fetch('/api/workflow/reset', { method: 'POST' })
      setLastRunResult(null)
      setScenarioState({ running: false, name: null, logs: [], status: null })
      showToast('Workflow reset to default pipeline', 'info')
      await fetchWorkflow()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleAddTask = async (e) => {
    if (e) e.preventDefault()
    const tid = newTaskId.trim()
    if (!tid) {
      showToast('Task ID cannot be empty', 'error')
      return
    }
    const deps = newDependencies
      .split(',')
      .map(d => d.trim())
      .filter(d => d.length > 0)

    try {
      const res = await fetch('/api/workflow/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: tid,
          dependencies: deps,
          should_fail: newShouldFail,
          fail_message: newFailMessage
        })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to add task')
      showToast(`Task "${tid}" added to DAG`, 'success')
      setNewTaskId('')
      setNewDependencies('')
      setNewShouldFail(false)
      await fetchWorkflow()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleDeleteTask = async (taskId) => {
    try {
      const res = await fetch(`/api/workflow/tasks/${taskId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete task')
      showToast(`Task "${taskId}" removed from workflow`, 'info')
      await fetchWorkflow()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  // 1-Click Diagnostics: Ticket #DAG-701 (Upstream Failure Cascade Skip Deadlock)
  const runScenarioDag701 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #DAG-701: Upstream Failure Cascade Skip Deadlock',
        status: 'running',
        logs: [
          '[1/4] Applying 3-tier linear pipeline (extract [fails] -> transform -> load)...'
        ]
      })

      await fetch('/api/workflow/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template: 'cascade_fail' })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Pipeline configured: "extract" will raise RuntimeError.',
          'Expected Architectural Behavior:',
          '  When "extract" fails, "transform" and "load" must cascade to SKIPPED.',
          '  skipped_tasks list should contain: ["transform", "load"].',
          '[2/4] Executing workflow via /api/workflow/run...'
        ]
      }))

      const res = await fetch('/api/workflow/run', { method: 'POST' })
      const data = await res.json()
      setLastRunResult(data)
      if (data.tasks) setTasks(data.tasks)

      const skipped = data.skipped_tasks || []
      const failed = data.failed_tasks || []

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Failed tasks reported: [${failed.join(', ')}]`,
          `Skipped tasks reported: [${skipped.join(', ')}]`
        ]
      }))

      if (!skipped.includes('transform') || !skipped.includes('load')) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            '🚨 VULNERABILITY DETECTED! Downstream tasks were NOT marked SKIPPED!',
            `Expected skipped: ["transform", "load"], but received: [${skipped.join(', ')}].`,
            'ROOT CAUSE: When task fails, executor does not traverse downstream dependencies to cascade SKIPPED status.',
            'Dependent tasks remain stranded in PENDING forever!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            '🛡️ PROTECTED! Direct and transitive downstream tasks properly cascaded to SKIPPED.',
            'SUCCESS: cascade_skip recursion successfully marked all dependents as SKIPPED.'
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

  // 1-Click Diagnostics: Ticket #DAG-702 (Premature Fan-In Dependency Execution)
  const runScenarioDag702 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #DAG-702: Premature Fan-In Dependency Execution',
        status: 'running',
        logs: [
          '[1/4] Applying fan-in topology (A [instant], X -> B [slow], C depends on A and B)...'
        ]
      })

      await fetch('/api/workflow/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template: 'fan_in' })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Topology loaded: C requires BOTH A and B.',
          'Expected Architectural Behavior:',
          '  Task C must wait until BOTH A and B have COMPLETED.',
          '  If executor uses `any()` instead of `all()`, C will fire prematurely as soon as A finishes, while B is still waiting on X!',
          '[2/4] Executing workflow...'
        ]
      }))

      const res = await fetch('/api/workflow/run', { method: 'POST' })
      const data = await res.json()
      setLastRunResult(data)
      if (data.tasks) setTasks(data.tasks)

      // Examine execution log order
      const eventLog = data.execution_log || []
      const cIndex = eventLog.findIndex(e => e.task_id === 'C' && e.event === 'RUNNING')
      const bIndex = eventLog.findIndex(e => e.task_id === 'B' && e.event === 'COMPLETED')

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Execution sequence: ${eventLog.map(e => `${e.task_id}:${e.event}`).join(' -> ')}`
        ]
      }))

      if (cIndex !== -1 && bIndex !== -1 && cIndex < bIndex) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            '🚨 VULNERABILITY DETECTED! Task C executed BEFORE dependency B completed!',
            'ROOT CAUSE: `elif any(dep in completed for dep in task.dependencies):` triggered ready status as soon as A finished.',
            'Conjunction error: Fan-in requires ALL dependencies to complete!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            '🛡️ PROTECTED! Task C waited until BOTH A and B completed.',
            'SUCCESS: `all(dep in completed for dep in task.dependencies)` enforced strict dependency conjunction.'
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

  // 1-Click Diagnostics: Ticket #DAG-703 (Disconnected Component Cycle Detection)
  const runScenarioDag703 = async () => {
    try {
      setScenarioState({
        running: true,
        name: 'Ticket #DAG-703: Disconnected Component Cycle Detection',
        status: 'running',
        logs: [
          '[1/3] Loading disconnected graph topology with cycle in secondary component...',
          'Component 1: "solo" (acyclic, independent)',
          'Component 2: "X" -> "Y" -> "X" (cyclic loop)'
        ]
      })

      await fetch('/api/workflow/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template: 'cycle' })
      })

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          '✓ Graph registered: 3 tasks total.',
          '[2/3] Querying workflow cycle detection engine...'
        ]
      }))

      const checkRes = await fetch('/api/workflow')
      const checkData = await checkRes.json()
      const detected = checkData.has_cycle

      setScenarioState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          `Engine detect_cycles() returned: ${detected}`
        ]
      }))

      if (!detected) {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'vulnerable',
          logs: [
            ...prev.logs,
            '🚨 VULNERABILITY DETECTED! Engine failed to detect cycle in secondary component!',
            'ROOT CAUSE: detect_cycles() only started DFS traversal from first_task_id ("solo").',
            'Because "solo" does not reach X or Y, the cycle in component 2 was never examined!'
          ]
        }))
      } else {
        setScenarioState(prev => ({
          ...prev,
          running: false,
          status: 'fixed',
          logs: [
            ...prev.logs,
            '🛡️ PROTECTED! Cycle accurately detected across all graph components.',
            'SUCCESS: Iterating over all unvisited tasks ensured complete topological coverage.'
          ]
        }))
      }
      await fetchWorkflow()
    } catch (err) {
      setScenarioState(prev => ({
        ...prev,
        running: false,
        status: 'error',
        logs: [...prev.logs, `Error: ${err.message}`]
      }))
    }
  }

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
              <circle cx="6" cy="6" r="3" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="12" r="3" />
              <line x1="8.5" y1="7.5" x2="15.5" y2="10.5" />
              <line x1="8.5" y1="16.5" x2="15.5" y2="13.5" />
            </svg>
          </div>
          <div>
            <div className="brand-title-wrap">
              <h1>TaskGraph Workflow DAG Studio</h1>
              <span className="badge-level">BH-L3-003</span>
              <span className="badge-env">ADVANCED</span>
            </div>
            <p className="brand-subtitle">
              Directed Acyclic Graph Engine • Fan-In Conjunction, Cycle Detection & Cascade Skips
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn btn-outline" onClick={fetchWorkflow} disabled={loading}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            Refresh
          </button>
          <button className="btn btn-primary" onClick={handleRunWorkflow} disabled={loading}>
            ▶ Run Workflow
          </button>
          <button className="btn btn-danger-outline" onClick={handleResetWorkflow}>
            Reset DAG
          </button>
        </div>
      </header>

      {/* Overview Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Graph Tasks</div>
          <div className="metric-value text-indigo">{tasks.length}</div>
          <div className="metric-foot">Registered nodes in DAG</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Topological Validation</div>
          <div className={`metric-value ${hasCycle ? 'text-red' : 'text-emerald'}`} style={{ fontSize: '1.6rem' }}>
            {hasCycle ? 'CYCLE DETECTED' : 'VALID DAG (ACYCLIC)'}
          </div>
          <div className="metric-foot">{hasCycle ? '3-color cycle detection failed' : 'Execution permitted'}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Last Execution Status</div>
          <div className={`metric-value ${!lastRunResult ? 'text-muted' : lastRunResult.is_successful ? 'text-emerald' : 'text-amber'}`} style={{ fontSize: '1.6rem' }}>
            {!lastRunResult ? 'READY' : lastRunResult.is_successful ? 'SUCCESS' : 'FAILED'}
          </div>
          <div className="metric-foot">
            {lastRunResult ? `${lastRunResult.completed_tasks.length} completed, ${lastRunResult.failed_tasks.length} failed, ${lastRunResult.skipped_tasks.length} skipped` : 'No runs executed'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Skipped Tasks</div>
          <div className="metric-value text-amber">
            {lastRunResult ? lastRunResult.skipped_tasks.length : 0}
          </div>
          <div className="metric-foot">Upstream failure cascades</div>
        </div>
      </div>

      {/* Preset Templates Bar */}
      <div className="templates-bar">
        <span className="templates-label">Topology Presets:</span>
        <button className="btn btn-template" onClick={() => handleApplyTemplate('default')}>
          Standard ETL
        </button>
        <button className="btn btn-template" onClick={() => handleApplyTemplate('diamond')}>
          Diamond Fan-Out/In
        </button>
        <button className="btn btn-template" onClick={() => handleApplyTemplate('cascade_fail')}>
          Cascade Skip Trap
        </button>
        <button className="btn btn-template" onClick={() => handleApplyTemplate('fan_in')}>
          Premature Fan-In Trap
        </button>
        <button className="btn btn-template" onClick={() => handleApplyTemplate('cycle')}>
          Disconnected Cycle Trap
        </button>
      </div>

      {/* Main Grid: Diagnostics & DAG Workspace */}
      <div className="dashboard-grid">
        {/* Left Column: Diagnostics & Task Creator */}
        <div className="column">
          {/* 1-Click Defect Reproduction Suite */}
          <div className="card">
            <div className="card-header">
              <h2>⚡ 1-Click Defect Reproduction Suite</h2>
              <span className="card-badge">DAG Diagnostics</span>
            </div>
            <div className="card-body">
              <p className="section-desc">
                Evaluate critical graph algorithms and failure handling before and after candidate fixes.
              </p>

              <div className="scenario-buttons">
                <button
                  className="scenario-btn"
                  onClick={runScenarioDag701}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-red"></span>
                    Ticket #DAG-701: Upstream Failure Cascade Skip Deadlock
                  </div>
                  <div className="scenario-btn-desc">
                    Verifies whether tasks downstream of a failure cascade to SKIPPED or remain stranded in PENDING.
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioDag702}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-amber"></span>
                    Ticket #DAG-702: Premature Fan-In on Partial Prerequisite
                  </div>
                  <div className="scenario-btn-desc">
                    Checks if multi-dependency tasks fire prematurely when only one dependency finishes (any vs all).
                  </div>
                </button>

                <button
                  className="scenario-btn"
                  onClick={runScenarioDag703}
                  disabled={scenarioState.running}
                >
                  <div className="scenario-btn-title">
                    <span className="dot dot-cyan"></span>
                    Ticket #DAG-703: Disconnected Component Cycle Detection
                  </div>
                  <div className="scenario-btn-desc">
                    Tests if cycle detection traverses all components or stops after the first task.
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

          {/* Add Task Form */}
          <div className="card">
            <div className="card-header">
              <h2>➕ Add Custom Workflow Task</h2>
              <span className="card-badge">POST /api/workflow/tasks</span>
            </div>
            <div className="card-body">
              <form onSubmit={handleAddTask}>
                <div className="form-group">
                  <label>Task ID</label>
                  <input
                    type="text"
                    value={newTaskId}
                    onChange={(e) => setNewTaskId(e.target.value)}
                    placeholder="e.g. validate_records"
                    className="text-input mono"
                  />
                </div>

                <div className="form-group">
                  <label>Prerequisite Dependencies (comma-separated)</label>
                  <input
                    type="text"
                    value={newDependencies}
                    onChange={(e) => setNewDependencies(e.target.value)}
                    placeholder="e.g. ingest, clean"
                    className="text-input mono"
                  />
                </div>

                <div className="checkbox-wrap">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={newShouldFail}
                      onChange={(e) => setNewShouldFail(e.target.checked)}
                    />
                    <span>Simulate Task Failure (Raises RuntimeError)</span>
                  </label>
                </div>

                {newShouldFail && (
                  <div className="form-group" style={{ marginTop: '0.75rem' }}>
                    <label>Simulated Error Message</label>
                    <input
                      type="text"
                      value={newFailMessage}
                      onChange={(e) => setNewFailMessage(e.target.value)}
                      className="text-input"
                    />
                  </div>
                )}

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
                  Register Task in DAG
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive DAG Topology & Execution State */}
        <div className="column">
          {/* Active Topology Cards */}
          <div className="card">
            <div className="card-header">
              <h2>🕸️ Active Workflow Topology & Task Nodes ({tasks.length})</h2>
              {hasCycle && <span className="status-pill status-pill-err">CYCLE DETECTED</span>}
            </div>
            <div className="card-body">
              <div className="tasks-grid">
                {tasks.length === 0 ? (
                  <div className="text-center text-muted" style={{ padding: '2rem' }}>
                    No tasks registered in workflow.
                  </div>
                ) : (
                  tasks.map((task) => {
                    const statusClass = 
                      task.status === 'COMPLETED' ? 'task-status-completed' :
                      task.status === 'FAILED' ? 'task-status-failed' :
                      task.status === 'SKIPPED' ? 'task-status-skipped' :
                      task.status === 'RUNNING' ? 'task-status-running' : 'task-status-pending'

                    return (
                      <div key={task.task_id} className={`task-node-card ${statusClass}`}>
                        <div className="task-node-header">
                          <div className="task-node-id mono">
                            <b>{task.task_id}</b>
                            {task.should_fail && <span className="badge-fail-tag">FAILS</span>}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className={`status-pill pill-${task.status.toLowerCase()}`}>
                              {task.status}
                            </span>
                            <button
                              className="btn-icon-delete"
                              onClick={() => handleDeleteTask(task.task_id)}
                              title="Delete Task"
                            >
                              ✕
                            </button>
                          </div>
                        </div>

                        <div className="task-node-body">
                          <div className="task-meta-row">
                            <span className="task-meta-key">Dependencies:</span>
                            <span className="mono">
                              {task.dependencies.length > 0 ? task.dependencies.join(', ') : <i className="text-dim">none (root)</i>}
                            </span>
                          </div>
                          <div className="task-meta-row">
                            <span className="task-meta-key">Downstream:</span>
                            <span className="mono">
                              {task.downstream.length > 0 ? task.downstream.join(', ') : <i className="text-dim">none (leaf)</i>}
                            </span>
                          </div>

                          {task.error && (
                            <div className="task-error-box mono">
                              Error: {task.error}
                            </div>
                          )}

                          {task.result && (
                            <div className="task-result-box mono">
                              Output: {task.result}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>

          {/* Execution Log & Results */}
          {lastRunResult && (
            <div className="card">
              <div className="card-header">
                <h2>📜 Execution Log & Event Stream</h2>
                <span className={`status-pill ${lastRunResult.is_successful ? 'status-pill-ok' : 'status-pill-err'}`}>
                  {lastRunResult.is_successful ? 'SUCCESSFUL' : 'FAILED'}
                </span>
              </div>
              <div className="card-body">
                {lastRunResult.error && (
                  <div className="task-error-box mono" style={{ marginBottom: '1rem' }}>
                    {lastRunResult.error}
                  </div>
                )}

                <div className="run-summary-row mono">
                  <div>Completed: <b>{lastRunResult.completed_tasks.length}</b> [{lastRunResult.completed_tasks.join(', ')}]</div>
                  <div>Failed: <b className="text-red">{lastRunResult.failed_tasks.length}</b> [{lastRunResult.failed_tasks.join(', ')}]</div>
                  <div>Skipped: <b className="text-amber">{lastRunResult.skipped_tasks.length}</b> [{lastRunResult.skipped_tasks.join(', ')}]</div>
                </div>

                {lastRunResult.execution_log && (
                  <div className="event-stream-box mono">
                    {lastRunResult.execution_log.map((ev, idx) => (
                      <div key={idx} className="event-stream-line">
                        <span className="text-dim">[{idx + 1}]</span> Task <b>{ev.task_id}</b> &rarr; <span className={`event-${ev.event.toLowerCase()}`}>{ev.event}</span>
                        {ev.error && <span className="text-red"> ({ev.error})</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

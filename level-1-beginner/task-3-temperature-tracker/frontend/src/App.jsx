import React, { useState, useEffect } from 'react'

const PRESET_SCENARIOS = [
  {
    id: 'weather-301',
    title: 'Ticket #WEATHER-301: Summer Readings (All > 0°C)',
    description: 'All recorded temps are between 18.5°C and 24.5°C. Starter bug incorrectly reports min_temp = 0.0°C!',
    readings: [18.5, 22.0, 24.5, 19.0, 21.5]
  },
  {
    id: 'weather-302',
    title: 'Ticket #WEATHER-302: Deep Freeze (All < 0°C)',
    description: 'Sub-zero polar readings between -15°C and -5.5°C. Starter bug incorrectly reports max_temp = 0.0°C!',
    readings: [-12.0, -8.5, -15.0, -5.5]
  },
  {
    id: 'weather-303',
    title: 'Ticket #WEATHER-303: Empty Reading List (ZeroDivisionError)',
    description: 'Sensor disconnection results in empty readings []. Starter code crashes on total / len(readings)!',
    readings: []
  },
  {
    id: 'weather-304',
    title: 'Mixed Spring Temperatures',
    description: 'Transition readings spanning below and above freezing.',
    readings: [-2.5, 0.0, 5.5, 8.0, 12.0]
  }
]

export default function App() {
  const [readings, setReadings] = useState(PRESET_SCENARIOS[0].readings)
  const [activeScenario, setActiveScenario] = useState('weather-301')
  const [newTemp, setNewTemp] = useState('')
  const [stats, setStats] = useState(null)
  const [serverStatus, setServerStatus] = useState('checking')
  const [error, setError] = useState(null)

  // Health check
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(() => setServerStatus('online'))
      .catch(() => setServerStatus('offline'))
  }, [])

  // Analyze whenever readings change
  useEffect(() => {
    analyze()
  }, [readings])

  const analyze = async () => {
    setError(null)
    try {
      const response = await fetch('/api/temperature/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ readings })
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Analysis failed.')
      }

      const data = await response.json()
      setStats(data.stats)
    } catch (err) {
      setStats(null)
      setError(err.message)
    }
  }

  const loadScenario = (sc) => {
    setActiveScenario(sc.id)
    setReadings(sc.readings)
  }

  const handleAddTemp = (e) => {
    e.preventDefault()
    if (!newTemp.trim()) return
    const num = parseFloat(newTemp)
    if (isNaN(num)) return

    setReadings([...readings, num])
    setNewTemp('')
    setActiveScenario('custom')
  }

  const handleRemoveTemp = (index) => {
    setReadings(readings.filter((_, i) => i !== index))
    setActiveScenario('custom')
  }

  // Mathematics truth evaluation
  const trueMin = readings.length > 0 ? Math.min(...readings) : null
  const trueMax = readings.length > 0 ? Math.max(...readings) : null
  const allPositive = readings.length > 0 && readings.every(t => t > 0)
  const allNegative = readings.length > 0 && readings.every(t => t < 0)

  // Bug Detection Flags
  const isMinBugActive = stats && allPositive && stats.min_temp === 0.0 && trueMin > 0.0
  const isMaxBugActive = stats && allNegative && stats.max_temp === 0.0 && trueMax < 0.0
  const isZeroDivBugActive = readings.length === 0 && error && error.includes('ZeroDivisionError')

  const isAnyBugActive = isMinBugActive || isMaxBugActive || isZeroDivBugActive
  const isClean = stats && !isAnyBugActive && (readings.length === 0 || (stats.min_temp === trueMin && stats.max_temp === trueMax))

  return (
    <div className="container">
      {/* Header */}
      <header className="app-header">
        <div className="title-group">
          <h1><span>🌡️</span> WeatherStation Studio</h1>
          <p>Bug Hunt Level 1 — Task 3: Extrema Tracking & Sentinel Initialization</p>
        </div>
        <div className="status-badge">
          <span className={`status-dot ${serverStatus === 'online' ? 'status-online' : 'status-offline'}`}></span>
          <span>API: {serverStatus === 'online' ? 'Connected (Port 8000)' : 'Offline / Standby'}</span>
        </div>
      </header>

      {/* Preset Scenarios */}
      <div className="scenario-bar">
        <div className="scenario-label">Bug Reproduction & Verification Scenarios</div>
        <div className="scenario-buttons">
          {PRESET_SCENARIOS.map(sc => (
            <button
              key={sc.id}
              className={`scenario-btn ${activeScenario === sc.id ? 'active' : ''}`}
              onClick={() => loadScenario(sc)}
            >
              <span>🎯</span>
              <span>{sc.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid-layout">
        {/* Left Column: Sensor Readings Feed */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem' }}>📡 Sensor Readings Feed ({readings.length})</h3>
            {readings.length > 0 && (
              <button
                className="pill-del"
                onClick={() => { setReadings([]); setActiveScenario('custom'); }}
                style={{ fontSize: '0.8rem', color: 'var(--danger)', cursor: 'pointer' }}
              >
                Clear All
              </button>
            )}
          </div>

          <div style={{ minHeight: '120px', padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '12px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
            {readings.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '36px 12px' }}>
                No temperature readings recorded (empty list <code>[]</code>).
              </div>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                {readings.map((t, idx) => (
                  <span key={idx} className={`reading-pill mono ${t <= 0 ? 'freezing' : 'warm'}`}>
                    <span>{t > 0 ? `+${t.toFixed(1)}` : t.toFixed(1)}°C</span>
                    <button className="pill-del" onClick={() => handleRemoveTemp(idx)} title="Remove reading">
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Add Reading Form */}
          <form onSubmit={handleAddTemp} style={{ display: 'flex', gap: '10px' }}>
            <input
              type="number"
              step="0.1"
              className="form-input mono"
              placeholder="Enter temp in °C (e.g. 21.5, -4.0)"
              value={newTemp}
              onChange={(e) => setNewTemp(e.target.value)}
            />
            <button type="submit" className="scenario-btn" style={{ padding: '10px 18px', whiteSpace: 'nowrap' }}>
              + Add Reading
            </button>
          </form>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5', marginTop: '14px' }}>
            💡 <strong>Observation Guide:</strong> Notice how initializing <code>min_temp = 0.0</code> fails when all values are positive (e.g. 20°C, 25°C), and <code>max_temp = 0.0</code> fails when all values are sub-zero (e.g. -10°C, -5°C).
          </div>
        </div>

        {/* Right Column: Statistics & Live Bug Detection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem' }}>📊 Extrema & Stats</h3>
              {stats && (
                <span className={`status-badge ${stats.is_freezing ? 'status-offline' : 'status-online'}`}>
                  {stats.is_freezing ? '❄️ FREEZING DETECTED' : '☀️ ABOVE FREEZING'}
                </span>
              )}
            </div>

            {error ? (
              <div style={{ padding: '14px', background: 'var(--danger-bg)', border: '1px solid rgba(239, 68, 68, 0.35)', borderRadius: '10px', marginTop: '16px', color: '#fca5a5' }}>
                <strong>⚠️ Backend Error:</strong>
                <p className="mono" style={{ fontSize: '0.85rem', marginTop: '6px' }}>{error}</p>
              </div>
            ) : stats ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-label">Minimum Temp</span>
                  <span className="stat-value mono" style={{ color: isMinBugActive ? 'var(--danger)' : '#38bdf8' }}>
                    {stats.min_temp !== null ? `${stats.min_temp.toFixed(1)}°C` : 'N/A'}
                  </span>
                  {isMinBugActive && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--danger)' }}>
                      Expected {trueMin.toFixed(1)}°C
                    </span>
                  )}
                </div>

                <div className="stat-card">
                  <span className="stat-label">Maximum Temp</span>
                  <span className="stat-value mono" style={{ color: isMaxBugActive ? 'var(--danger)' : '#f97316' }}>
                    {stats.max_temp !== null ? `${stats.max_temp.toFixed(1)}°C` : 'N/A'}
                  </span>
                  {isMaxBugActive && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--danger)' }}>
                      Expected {trueMax.toFixed(1)}°C
                    </span>
                  )}
                </div>

                <div className="stat-card">
                  <span className="stat-label">Average Temp</span>
                  <span className="stat-value mono">
                    {stats.avg_temp !== null ? `${stats.avg_temp.toFixed(1)}°C` : 'N/A'}
                  </span>
                </div>

                <div className="stat-card">
                  <span className="stat-label">Total Readings</span>
                  <span className="stat-value mono">
                    {stats.reading_count}
                  </span>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                Awaiting calculation...
              </div>
            )}
          </div>

          {/* Live Bug Detection */}
          <div className="glass-panel">
            <h3 style={{ marginBottom: '12px', fontSize: '1.05rem' }}>🔬 Live Bug Detection</h3>
            {isMinBugActive ? (
              <div className="alert-banner alert-danger">
                <div className="alert-icon">🐞</div>
                <div className="alert-content">
                  <h4 style={{ color: 'var(--danger)' }}>Defect Active: Zero Sentinel Minimum Fallthrough</h4>
                  <p>
                    Engine reported minimum temperature as <strong>0.0°C</strong>, but every single reading was above freezing (actual lowest reading is <strong>{trueMin.toFixed(1)}°C</strong>)!
                  </p>
                  <p style={{ marginTop: '8px', color: '#fca5a5' }} className="mono">
                    Fix Location: src/temperature_analyzer.py lines 31-33
                  </p>
                </div>
              </div>
            ) : isMaxBugActive ? (
              <div className="alert-banner alert-danger">
                <div className="alert-icon">🐞</div>
                <div className="alert-content">
                  <h4 style={{ color: 'var(--danger)' }}>Defect Active: Zero Sentinel Maximum Fallthrough</h4>
                  <p>
                    Engine reported maximum temperature as <strong>0.0°C</strong> on deep freeze readings (actual highest reading is <strong>{trueMax.toFixed(1)}°C</strong>)!
                  </p>
                  <p style={{ marginTop: '8px', color: '#fca5a5' }} className="mono">
                    Fix Location: src/temperature_analyzer.py lines 31-33
                  </p>
                </div>
              </div>
            ) : isZeroDivBugActive ? (
              <div className="alert-banner alert-danger">
                <div className="alert-icon">💥</div>
                <div className="alert-content">
                  <h4 style={{ color: 'var(--danger)' }}>Defect Active: ZeroDivisionError on Empty List</h4>
                  <p>
                    Empty sensor reading list crashed the calculation engine because there was no guard check before dividing by <code>len(readings)</code>.
                  </p>
                  <p style={{ marginTop: '8px', color: '#fca5a5' }} className="mono">
                    Fix Location: src/temperature_analyzer.py line 20
                  </p>
                </div>
              </div>
            ) : isClean ? (
              <div className="alert-banner alert-success">
                <div className="alert-icon">✅</div>
                <div className="alert-content">
                  <h4 style={{ color: 'var(--success)' }}>Defect Resolved: Data-Driven Extrema & Empty Guard</h4>
                  <p>
                    Calculations are robust! Extrema initialized from real data points, and empty lists are cleanly handled without crashing.
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}

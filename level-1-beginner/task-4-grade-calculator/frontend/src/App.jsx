import React, { useState, useEffect } from 'react'

export default function App() {
  const [studentName, setStudentName] = useState('Alex Rivera')
  const [score, setScore] = useState('95.0')
  const [hasExtraCredit, setHasExtraCredit] = useState(false)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [apiOnline, setApiOnline] = useState(false)

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health')
        if (res.ok) {
          setApiOnline(true)
        } else {
          setApiOnline(false)
        }
      } catch {
        setApiOnline(false)
      }
    }
    checkHealth()
    const timer = setInterval(checkHealth, 5000)
    return () => clearInterval(timer)
  }, [])

  const handleCalculate = async (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('http://localhost:8000/api/grade/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_name: studentName,
          score: parseFloat(score),
          has_extra_credit: hasExtraCredit
        })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Calculation failed')
      }
      setReport(data)
    } catch (err) {
      setError(err.message)
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  // Load ticket scenarios
  const loadScenarioTopStudent = () => {
    setStudentName('Sarah Connor')
    setScore('95.0')
    setHasExtraCredit(false)
  }

  const loadScenarioBoundaryA = () => {
    setStudentName('Marcus Vance')
    setScore('90.0')
    setHasExtraCredit(false)
  }

  const loadScenarioExtraCredit = () => {
    setStudentName('Elena Rostova')
    setScore('86.0')
    setHasExtraCredit(true)
  }

  // Detect whether the bug is actively manifesting
  const numScore = parseFloat(score)
  const isBugActive = report && (
    (report.original_score >= 90.0 && report.letter_grade !== 'A') ||
    (report.original_score >= 80.0 && report.original_score < 90.0 && report.letter_grade !== 'B')
  )

  return (
    <div className="container">
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <h1>EduGrade Classifier</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Academic Performance & GPA Verification Service
            </p>
          </div>
        </div>

        <div className={`badge ${apiOnline ? 'online' : 'offline'}`}>
          <div className="badge-dot" />
          <span>{apiOnline ? 'API Connected (8000)' : 'API Offline (Run: python3 api.py)'}</span>
        </div>
      </header>

      <div className="grid-layout">
        {/* Left Column: Input Form & Scenarios */}
        <div>
          <div className="card">
            <h2 className="card-title">Grade Parameters</h2>
            <p className="card-subtitle">Enter student evaluation scores or load a reproduction ticket.</p>

            <form onSubmit={handleCalculate}>
              <div className="form-group">
                <label>Student Name</label>
                <input
                  type="text"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="e.g. Alex Rivera"
                  required
                />
              </div>

              <div className="form-group">
                <label>Numerical Score (0.0 — 100.0)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={score}
                  onChange={(e) => setScore(e.target.value)}
                  required
                />
              </div>

              <label className="checkbox-group">
                <input
                  type="checkbox"
                  checked={hasExtraCredit}
                  onChange={(e) => setHasExtraCredit(e.target.checked)}
                />
                <span>Award Extra Credit (+5.0 points, capped at 100.0)</span>
              </label>

              <button type="submit" className="btn btn-primary" disabled={loading || !apiOnline}>
                {loading ? 'Evaluating...' : 'Compute Official Grade'}
              </button>
            </form>
          </div>

          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h3 className="card-title" style={{ fontSize: '1rem' }}>Bug Reproduction Scenarios</h3>
            <p className="card-subtitle" style={{ marginBottom: '1rem' }}>
              Click to load scenarios reported in user tickets:
            </p>

            <button type="button" className="scenario-pill" onClick={loadScenarioTopStudent}>
              <strong>Ticket #EDU-101:</strong> Top Student 95% Fallthrough (Score: 95.0)
            </button>
            <button type="button" className="scenario-pill" onClick={loadScenarioBoundaryA}>
              <strong>Boundary Check:</strong> Exact Grade A Threshold (Score: 90.0)
            </button>
            <button type="button" className="scenario-pill" onClick={loadScenarioExtraCredit}>
              <strong>Extra Credit Boost:</strong> 86.0 + 5.0 Bonus = 91.0 (Grade A)
            </button>
          </div>
        </div>

        {/* Right Column: Grade Report & Bug Analysis */}
        <div>
          <div className="card result-card">
            <h2 className="card-title" style={{ justifyContent: 'center' }}>Official Grade Transcript</h2>
            <p className="card-subtitle">Generated by <code>src/grade_calculator.py</code></p>

            {error && (
              <div className="bug-alert" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5' }}>
                <strong>Error:</strong> {error}
              </div>
            )}

            {!report && !error && (
              <div style={{ padding: '3rem 1rem', color: 'var(--text-dim)' }}>
                <p>Click <strong>Compute Official Grade</strong> to generate the transcript.</p>
              </div>
            )}

            {report && (
              <>
                <div className={`grade-badge-display grade-${report.letter_grade}`}>
                  {report.letter_grade}
                </div>

                <div style={{ marginTop: '1rem', textAlign: 'left' }}>
                  <div className="stat-row">
                    <span className="stat-label">Student</span>
                    <span className="stat-val">{report.student_name}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Original Score</span>
                    <span className="stat-val">{report.original_score}%</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Letter Grade</span>
                    <span className="stat-val" style={{ color: 'var(--accent-light)' }}>
                      Grade {report.letter_grade}
                    </span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">GPA Scale (4.0)</span>
                    <span className="stat-val">{report.gpa_points.toFixed(1)}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Academic Status</span>
                    <span className="stat-val" style={{ color: report.is_passing ? 'var(--success)' : 'var(--danger)' }}>
                      {report.is_passing ? 'Passing' : 'Academic Probation (Failing)'}
                    </span>
                  </div>
                </div>

                {isBugActive ? (
                  <div className="bug-alert">
                    <div className="bug-title" style={{ color: 'var(--danger)' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                      Ticket #EDU-101 Bug Detected!
                    </div>
                    <p style={{ color: '#fca5a5' }}>
                      Student scored <strong>{report.original_score}%</strong> (should be Grade A), but was awarded <strong>Grade {report.letter_grade}</strong>!
                      <br /><br />
                      <strong>Root Cause:</strong> <code>src/grade_calculator.py</code> uses independent <code>if</code> statements instead of <code>elif</code>, causing the grade to fall through and get overwritten by lower grade checks.
                    </p>
                  </div>
                ) : (
                  <div className="bug-alert fixed">
                    <div className="bug-title" style={{ color: 'var(--success)' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                      Correct Evaluation
                    </div>
                    <p style={{ color: '#6ee7b7' }}>
                      The grade corresponds accurately to the student's performance tier.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

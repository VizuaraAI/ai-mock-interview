import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, Award, Brain, Target, Users, BookOpen } from 'lucide-react'
import { getReport } from '../api/client'

function ScoreBar({ label, score, max = 100, icon: Icon }) {
  const pct = Math.min((score / max) * 100, 100)
  const color =
    pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-gray-300">
          {Icon && <Icon size={14} />}
          {label}
        </div>
        <span className="text-gray-400">
          {score}/{max}
        </span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function Report() {
  const { sessionId } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getReport(sessionId)
        setReport(data)
      } catch (err) {
        setError(err.response?.data?.detail || err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchReport()
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4" size={32} />
          <p className="text-gray-400">Generating your evaluation report...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <p className="text-red-400">Error: {error}</p>
      </div>
    )
  }

  const ps = report.phase_scores

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-semibold tracking-tight mb-2">Interview Report</h1>
        <p className="text-gray-400 mb-10">Your evaluation across all interview phases.</p>

        {/* Overall Score */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 mb-8 text-center">
          <div className="text-6xl font-bold mb-2">
            {report.overall_score}
            <span className="text-2xl text-gray-500">/100</span>
          </div>
          <p className="text-gray-400">Overall Composite Score</p>
          <p className="text-xs text-gray-600 mt-2">
            Phase 2 (30%) + Phase 3 (25%) + Phase 4 (25%) + Phase 5 (20%)
          </p>
        </div>

        {/* Phase 2 */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-4">
          <h2 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Brain size={16} /> Phase 2: Technical Deep-Dive (Project 1)
          </h2>
          <div className="space-y-3">
            <ScoreBar label="Socrates Depth" score={ps.phase2_socrates_depth} icon={Target} />
            <ScoreBar label="Hint Utilization" score={ps.phase2_hint_utilization} icon={BookOpen} />
          </div>
        </div>

        {/* Phase 3 */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-4">
          <h2 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Brain size={16} /> Phase 3: Technical Deep-Dive (Project 2)
          </h2>
          <div className="space-y-3">
            <ScoreBar label="Socrates Depth" score={ps.phase3_socrates_depth} icon={Target} />
            <ScoreBar label="Hint Utilization" score={ps.phase3_hint_utilization} icon={BookOpen} />
          </div>
        </div>

        {/* Phase 4 */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-4">
          <h2 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Award size={16} /> Phase 4: Factual ML Questions
          </h2>
          <ScoreBar label="Accuracy" score={ps.phase4_factual_accuracy} />

          {report.details?.phase4?.question_results?.length > 0 && (
            <div className="mt-4 space-y-2">
              {report.details.phase4.question_results.map((qr, i) => (
                <div key={i} className="text-xs flex items-start gap-2">
                  <span className={qr.correct ? 'text-emerald-400' : 'text-red-400'}>
                    {qr.correct ? '✓' : '✗'}
                  </span>
                  <div>
                    <span className="text-gray-400">{qr.question}</span>
                    <span className="text-gray-600 ml-2">— {qr.explanation}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phase 5 */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
          <h2 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Users size={16} /> Phase 5: Behavioral Assessment
          </h2>
          <div className="space-y-3">
            <ScoreBar label="Visionary Thinking" score={ps.phase5_visionary} max={5} />
            <ScoreBar label="Groundedness" score={ps.phase5_groundedness} max={5} />
            <ScoreBar label="Team Player" score={ps.phase5_team_player} max={5} />
          </div>
        </div>

        <button
          onClick={() => window.location.href = '/'}
          className="w-full py-3 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
        >
          Start New Interview
        </button>
      </div>
    </div>
  )
}

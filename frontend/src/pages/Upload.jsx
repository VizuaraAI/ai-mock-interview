import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, FileText, Loader2 } from 'lucide-react'
import { uploadResume, startInterview } from '../api/client'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [parsed, setParsed] = useState(null)
  const [candidateId, setCandidateId] = useState(null)
  const navigate = useNavigate()

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped?.type === 'application/pdf') setFile(dropped)
  }, [])

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setStatus('Parsing resume with AI...')
    try {
      const data = await uploadResume(file)
      setParsed(data.parsed_resume)
      setCandidateId(data.candidate_id)
      setStatus('Resume parsed successfully.')
    } catch (err) {
      setStatus('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleStartInterview = async () => {
    setLoading(true)
    setStatus('Starting interview...')
    try {
      const data = await startInterview(candidateId)
      navigate(`/interview/${data.session_id}`, {
        state: { firstMessage: data.interviewer_message, phase: data.phase },
      })
    } catch (err) {
      setStatus('Error: ' + (err.response?.data?.detail || err.message))
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-semibold tracking-tight mb-2">AI Mock Interview</h1>
        <p className="text-gray-400 mb-10">Upload your resume to begin a technical ML engineering interview.</p>

        {!parsed ? (
          <>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input').click()}
              className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-colors
                ${dragOver ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-500'}`}
            >
              <input
                id="file-input"
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setFile(e.target.files[0])}
              />
              <UploadIcon className="mx-auto mb-4 text-gray-500" size={40} />
              {file ? (
                <div className="flex items-center justify-center gap-2 text-gray-300">
                  <FileText size={18} />
                  <span>{file.name}</span>
                </div>
              ) : (
                <p className="text-gray-500">Drop your resume PDF here or click to browse</p>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="mt-6 w-full py-3 rounded-lg bg-white text-gray-950 font-medium
                disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-200 transition-colors"
            >
              {loading ? <Loader2 className="mx-auto animate-spin" size={20} /> : 'Upload & Parse Resume'}
            </button>
          </>
        ) : (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-medium mb-4">{parsed.name}</h2>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-400">
                <div><span className="text-gray-500">Email:</span> {parsed.email}</div>
                <div><span className="text-gray-500">Phone:</span> {parsed.phone}</div>
              </div>

              {parsed.education?.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Education</h3>
                  {parsed.education.map((edu, i) => (
                    <div key={i} className="text-sm text-gray-400">
                      {edu.degree} — {edu.institution} ({edu.duration})
                    </div>
                  ))}
                </div>
              )}

              {parsed.experience?.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Experience</h3>
                  {parsed.experience.map((exp, i) => (
                    <div key={i} className="text-sm text-gray-400 mb-2">
                      <span className="text-gray-300">{exp.role}</span> at {exp.company} ({exp.duration})
                    </div>
                  ))}
                </div>
              )}

              {parsed.projects?.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Projects</h3>
                  {parsed.projects.map((proj, i) => (
                    <div key={i} className="text-sm text-gray-400 mb-1">
                      {proj.name}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleStartInterview}
              disabled={loading}
              className="w-full py-3 rounded-lg bg-white text-gray-950 font-medium
                disabled:opacity-40 hover:bg-gray-200 transition-colors"
            >
              {loading ? <Loader2 className="mx-auto animate-spin" size={20} /> : 'Start Interview'}
            </button>
          </div>
        )}

        {status && <p className="mt-4 text-sm text-gray-500">{status}</p>}
      </div>
    </div>
  )
}

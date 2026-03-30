import { useState, useEffect, useRef } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { Mic, MicOff, Send, Loader2, Volume2 } from 'lucide-react'
import { sendResponse, transcribeAudio, synthesizeSpeech } from '../api/client'

const PHASE_LABELS = {
  1: 'Phase 1: Background',
  2: 'Phase 2: Project Deep-Dive',
  3: 'Phase 3: Project Deep-Dive II',
  4: 'Phase 4: Factual Questions',
  5: 'Phase 5: Behavioral',
}

export default function Interview() {
  const { sessionId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState(1)
  const [depthLevel, setDepthLevel] = useState(0)
  const [recording, setRecording] = useState(false)
  const [playingAudio, setPlayingAudio] = useState(false)
  const [anxietyAlert, setAnxietyAlert] = useState(null)
  const messagesEndRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    if (location.state?.firstMessage) {
      const msg = { role: 'interviewer', content: location.state.firstMessage }
      setMessages([msg])
      setPhase(location.state.phase || 1)
      playTTS(location.state.firstMessage)
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const playTTS = async (text) => {
    try {
      setPlayingAudio(true)
      const audioBlob = await synthesizeSpeech(text)
      const url = URL.createObjectURL(audioBlob)
      const audio = new Audio(url)
      audio.onended = () => {
        setPlayingAudio(false)
        URL.revokeObjectURL(url)
      }
      audio.onerror = () => setPlayingAudio(false)
      await audio.play()
    } catch {
      setPlayingAudio(false)
    }
  }

  const handleSend = async (text, speechRate = null) => {
    if (!text.trim() || loading) return

    const userMsg = { role: 'candidate', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await sendResponse(sessionId, text, speechRate)
      setPhase(data.phase)
      if (data.depth_level) setDepthLevel(data.depth_level)

      if (data.status === 'completed') {
        const interviewerMsg = { role: 'interviewer', content: data.interviewer_message }
        setMessages((prev) => [...prev, interviewerMsg])
        await playTTS(data.interviewer_message)
        setTimeout(() => navigate(`/report/${sessionId}`), 3000)
        return
      }

      const interviewerMsg = { role: 'interviewer', content: data.interviewer_message }
      setMessages((prev) => [...prev, interviewerMsg])
      await playTTS(data.interviewer_message)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'system', content: 'Error: ' + (err.response?.data?.detail || err.message) },
      ])
    } finally {
      setLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach((t) => t.stop())

        setLoading(true)
        try {
          const result = await transcribeAudio(blob)

          // Check anxiety
          if (result.anxiety?.is_anxious) {
            setAnxietyAlert(result.anxiety.calming_message)
            setTimeout(() => setAnxietyAlert(null), 6000)
          }

          if (result.text) {
            await handleSend(result.text, result.speech_rate_wpm)
          }
        } catch (err) {
          setMessages((prev) => [
            ...prev,
            { role: 'system', content: 'Transcription error: ' + err.message },
          ])
          setLoading(false)
        }
      }

      mediaRecorder.start()
      setRecording(true)
    } catch {
      alert('Microphone access denied.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
      setRecording(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Phase Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-blue-400">{PHASE_LABELS[phase]}</span>
          {phase >= 2 && phase <= 3 && (
            <span className="ml-3 text-xs text-gray-500">Depth: {depthLevel}</span>
          )}
        </div>
        {playingAudio && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Volume2 size={14} className="animate-pulse" /> Speaking...
          </div>
        )}
      </div>

      {/* Anxiety Alert */}
      {anxietyAlert && (
        <div className="bg-amber-900/30 border-b border-amber-800 px-6 py-3 text-sm text-amber-200">
          {anxietyAlert}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'candidate' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                ${msg.role === 'candidate'
                  ? 'bg-blue-600 text-white'
                  : msg.role === 'system'
                    ? 'bg-red-900/50 text-red-200'
                    : 'bg-gray-800 text-gray-200'
                }`}
            >
              {msg.role === 'interviewer' && (
                <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-wide">Interviewer</div>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl px-4 py-3">
              <Loader2 className="animate-spin text-gray-400" size={18} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="border-t border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <button
            onClick={recording ? stopRecording : startRecording}
            disabled={loading}
            className={`p-3 rounded-full transition-colors
              ${recording
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
              } disabled:opacity-40`}
          >
            {recording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder={recording ? 'Recording...' : 'Type your response...'}
            disabled={loading || recording}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm
              placeholder-gray-500 focus:outline-none focus:border-gray-600
              disabled:opacity-40"
          />

          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || loading}
            className="p-3 rounded-full bg-white text-gray-950 hover:bg-gray-200 transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function uploadResume(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload-resume', form)
  return data
}

export async function startInterview(candidateId) {
  const { data } = await api.post('/interview/start', { candidate_id: candidateId })
  return data
}

export async function sendResponse(sessionId, message, speechRate = null) {
  const { data } = await api.post('/interview/respond', {
    session_id: sessionId,
    message,
    speech_rate: speechRate,
  })
  return data
}

export async function getReport(sessionId) {
  const { data } = await api.get(`/interview/${sessionId}/report`)
  return data
}

export async function transcribeAudio(audioBlob) {
  const form = new FormData()
  form.append('file', audioBlob, 'recording.webm')
  const { data } = await api.post('/voice/transcribe', form)
  return data
}

export async function synthesizeSpeech(text) {
  const response = await api.post('/voice/synthesize', { text }, { responseType: 'blob' })
  return response.data
}

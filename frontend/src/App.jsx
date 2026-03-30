import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Upload from './pages/Upload'
import Interview from './pages/Interview'
import Report from './pages/Report'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/interview/:sessionId" element={<Interview />} />
        <Route path="/report/:sessionId" element={<Report />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

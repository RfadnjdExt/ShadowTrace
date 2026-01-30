import { useState, useEffect } from 'react'
import UploadZone from './components/UploadZone'
import SessionList from './components/SessionList'
import ChatView from './components/ChatView'

const API_BASE = '/api'

function App() {
    const [sessions, setSessions] = useState([])
    const [selectedSession, setSelectedSession] = useState(null)
    const [loading, setLoading] = useState(false)
    const [view, setView] = useState('list') // list | chat

    useEffect(() => {
        fetchSessions()
    }, [])

    const fetchSessions = async () => {
        try {
            const res = await fetch(`${API_BASE}/sessions`)
            const data = await res.json()
            setSessions(data)
        } catch (err) {
            console.error('Failed to fetch sessions:', err)
        }
    }

    const handleUpload = async (file) => {
        setLoading(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch(`${API_BASE}/sessions/upload`, {
                method: 'POST',
                body: formData,
            })

            if (res.ok) {
                await fetchSessions()
            }
        } catch (err) {
            console.error('Upload failed:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleSelectSession = async (session) => {
        setSelectedSession(session)
        setView('chat')
    }

    const handleAnalyze = async (sessionId) => {
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE}/sessions/${sessionId}/analyze`, {
                method: 'POST',
            })

            if (res.ok) {
                await fetchSessions()
                // Refresh selected session
                const sessionRes = await fetch(`${API_BASE}/sessions/${sessionId}`)
                const updated = await sessionRes.json()
                setSelectedSession(updated)
            }
        } catch (err) {
            console.error('Analysis failed:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleBack = () => {
        setView('list')
        setSelectedSession(null)
        fetchSessions()
    }

    return (
        <div className="app">
            <header className="header">
                <h1>
                    <span>Shadow</span>Trace
                </h1>
                {view === 'chat' && (
                    <button className="btn btn-secondary" onClick={handleBack}>
                        Back to Sessions
                    </button>
                )}
            </header>

            <main className="container">
                {view === 'list' ? (
                    <>
                        <UploadZone onUpload={handleUpload} loading={loading} />
                        <SessionList
                            sessions={sessions}
                            onSelect={handleSelectSession}
                        />
                    </>
                ) : (
                    <ChatView
                        session={selectedSession}
                        onAnalyze={handleAnalyze}
                        loading={loading}
                    />
                )}
            </main>
        </div>
    )
}

export default App

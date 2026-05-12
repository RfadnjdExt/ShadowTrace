import { useState, useEffect, useCallback } from 'react'
import UploadZone from './components/UploadZone'
import SessionList from './components/SessionList'
import ChatView from './components/ChatView'
import Toast from './components/Toast'

const API_BASE = '/api'

function App() {
    const [sessions, setSessions] = useState([])
    const [selectedSession, setSelectedSession] = useState(null)
    const [loading, setLoading] = useState(false)
    const [view, setView] = useState('list')
    const [toasts, setToasts] = useState([])

    const addToast = useCallback((message, type = 'info') => {
        const id = Date.now()
        setToasts(prev => [...prev, { id, message, type }])
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 4000)
    }, [])

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    useEffect(() => {
        fetchSessions()
    }, [])

    const fetchSessions = async () => {
        try {
            const res = await fetch(`${API_BASE}/sessions`)
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            const data = await res.json()
            setSessions(data)
        } catch (err) {
            addToast('Gagal memuat sessions. Pastikan backend berjalan.', 'error')
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
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || `HTTP ${res.status}`)
            }
            await fetchSessions()
            addToast(`File "${file.name}" berhasil diupload!`, 'success')
        } catch (err) {
            addToast(`Upload gagal: ${err.message}`, 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleSelectSession = (session) => {
        setSelectedSession(session)
        setView('chat')
    }

    const handleAnalyze = async (sessionId) => {
        setLoading(true)
        addToast('Menjalankan analisis forensik...', 'info')
        try {
            const res = await fetch(`${API_BASE}/sessions/${sessionId}/analyze`, {
                method: 'POST',
            })
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || `HTTP ${res.status}`)
            }
            const result = await res.json()
            await fetchSessions()
            const sessionRes = await fetch(`${API_BASE}/sessions/${sessionId}`)
            const updated = await sessionRes.json()
            setSelectedSession(updated)
            addToast(
                `Analisis selesai! ${result.gaps_detected} gap, ${result.inferences_generated} inferensi AI.`,
                'success'
            )
        } catch (err) {
            addToast(`Analisis gagal: ${err.message}`, 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteSession = async (sessionId) => {
        try {
            const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            await fetchSessions()
            addToast('Session berhasil dihapus.', 'success')
        } catch (err) {
            addToast(`Gagal menghapus: ${err.message}`, 'error')
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
                <div className="header-brand">
                    <div className="header-logo">ST</div>
                    <div>
                        <h1><span>Shadow</span>Trace</h1>
                        <span className="header-tagline">Forensic Chat Reconstructor</span>
                    </div>
                </div>
                {view === 'chat' && (
                    <button className="btn btn-secondary" onClick={handleBack}>
                        ← Sessions
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
                            onDelete={handleDeleteSession}
                            onRefresh={fetchSessions}
                        />
                    </>
                ) : (
                    <ChatView
                        session={selectedSession}
                        onAnalyze={handleAnalyze}
                        loading={loading}
                        addToast={addToast}
                    />
                )}
            </main>

            <div className="toast-container">
                {toasts.map(t => (
                    <Toast key={t.id} toast={t} onRemove={removeToast} />
                ))}
            </div>
        </div>
    )
}

export default App

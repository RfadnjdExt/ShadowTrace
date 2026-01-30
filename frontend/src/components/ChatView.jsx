import { useState, useEffect } from 'react'
import GapCard from './GapCard'

const API_BASE = '/api'

function ChatView({ session, onAnalyze, loading }) {
    const [messages, setMessages] = useState([])
    const [gaps, setGaps] = useState([])
    const [inferences, setInferences] = useState({})
    const [stats, setStats] = useState(null)

    useEffect(() => {
        if (session?.id) {
            fetchData()
        }
    }, [session?.id])

    const fetchData = async () => {
        try {
            // Fetch messages
            const msgRes = await fetch(`${API_BASE}/sessions/${session.id}/messages?limit=500`)
            const msgData = await msgRes.json()
            setMessages(msgData)

            // Fetch gaps
            const gapRes = await fetch(`${API_BASE}/sessions/${session.id}/gaps`)
            const gapData = await gapRes.json()
            setGaps(gapData)

            // Fetch inferences
            const infRes = await fetch(`${API_BASE}/sessions/${session.id}/inferences`)
            const infData = await infRes.json()

            // Map by gap_id
            const infMap = {}
            infData.forEach(inf => {
                infMap[inf.gap_id] = inf
            })
            setInferences(infMap)

            // Fetch stats
            const statRes = await fetch(`${API_BASE}/sessions/${session.id}/stats`)
            const statData = await statRes.json()
            setStats(statData)

        } catch (err) {
            console.error('Failed to fetch data:', err)
        }
    }

    // Build gap lookup by sequence
    const gapsBySeq = {}
    gaps.forEach(gap => {
        gapsBySeq[gap.after_message_seq] = gap
    })

    const formatTime = (dateStr) => {
        return new Date(dateStr).toLocaleTimeString('id-ID', {
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        })
    }

    return (
        <div>
            {/* Stats Bar */}
            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{stats.total_messages}</div>
                        <div className="stat-label">Messages</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--warning)' }}>
                            {gaps.length}
                        </div>
                        <div className="stat-label">Gaps Detected</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--danger)' }}>
                            {stats.deleted_messages}
                        </div>
                        <div className="stat-label">Deleted</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">
                            {Object.keys(stats.participants || {}).length}
                        </div>
                        <div className="stat-label">Participants</div>
                    </div>
                </div>
            )}

            {/* Analyze Button */}
            {session.status !== 'analyzed' && (
                <div style={{ marginBottom: '1rem' }}>
                    <button
                        className="btn btn-primary"
                        onClick={() => onAnalyze(session.id)}
                        disabled={loading}
                    >
                        {loading ? 'Analyzing...' : 'Analyze for Gaps'}
                    </button>
                </div>
            )}

            {/* Main Content */}
            <div className="chat-container">
                {/* Messages Panel */}
                <div className="messages-panel">
                    {messages.map((msg) => {
                        const hasGapBefore = gapsBySeq[msg.sequence_number]

                        return (
                            <div key={msg.id}>
                                {hasGapBefore && (
                                    <div className="gap-indicator">
                                        Gap detected: {Math.round(hasGapBefore.time_gap_seconds / 60)} min
                                        {hasGapBefore.expected_messages &&
                                            ` (~${hasGapBefore.expected_messages} messages missing)`
                                        }
                                    </div>
                                )}
                                <div className={`message ${msg.is_deleted ? 'deleted' : ''}`}>
                                    <div className="message-header">
                                        <span className="message-sender">{msg.sender}</span>
                                        <span className="message-time">
                                            {formatDate(msg.timestamp)} {formatTime(msg.timestamp)}
                                        </span>
                                    </div>
                                    <div className="message-content">
                                        {msg.is_deleted ? '[Pesan dihapus]' : msg.content}
                                    </div>
                                </div>
                            </div>
                        )
                    })}

                    {messages.length === 0 && (
                        <div className="loading">No messages found</div>
                    )}
                </div>

                {/* Gaps Sidebar */}
                <div className="sidebar-panel">
                    <h3 style={{ marginBottom: '0.5rem' }}>Detected Gaps</h3>

                    {gaps.length === 0 ? (
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            {session.status === 'analyzed'
                                ? 'No suspicious gaps found'
                                : 'Run analysis to detect gaps'}
                        </p>
                    ) : (
                        gaps.map(gap => (
                            <GapCard
                                key={gap.id}
                                gap={gap}
                                inference={inferences[gap.id]}
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}

export default ChatView

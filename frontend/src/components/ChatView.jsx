import { useState, useEffect, useRef } from 'react'
import GapCard from './GapCard'

const API_BASE = '/api'

function ChatView({ session, onAnalyze, loading, addToast }) {
    const [messages, setMessages] = useState([])
    const [gaps, setGaps] = useState([])
    const [inferences, setInferences] = useState({})
    const [stats, setStats] = useState(null)
    const [fetching, setFetching] = useState(false)

    // Filter & search state
    const [search, setSearch] = useState('')
    const [filterSender, setFilterSender] = useState('all')
    const [filterType, setFilterType] = useState('all') // all | deleted | gap
    const [highlightedGap, setHighlightedGap] = useState(null)

    const messagesEndRef = useRef(null)

    useEffect(() => {
        if (session?.id) fetchData()
    }, [session?.id])

    const fetchData = async () => {
        setFetching(true)
        try {
            const [msgRes, gapRes, infRes, statRes] = await Promise.all([
                fetch(`${API_BASE}/sessions/${session.id}/messages?limit=1000`),
                fetch(`${API_BASE}/sessions/${session.id}/gaps`),
                fetch(`${API_BASE}/sessions/${session.id}/inferences`),
                fetch(`${API_BASE}/sessions/${session.id}/stats`),
            ])

            const msgData = await msgRes.json()
            const gapData = await gapRes.json()
            const infData = await infRes.json()
            const statData = await statRes.json()

            setMessages(msgData)
            setGaps(gapData)

            const infMap = {}
            infData.forEach(inf => { infMap[inf.gap_id] = inf })
            setInferences(infMap)
            setStats(statData)
        } catch (err) {
            addToast?.('Gagal memuat data chat.', 'error')
        } finally {
            setFetching(false)
        }
    }

    // Derived data
    const senders = [...new Set(messages.map(m => m.sender).filter(Boolean))]

    const gapsBySeq = {}
    gaps.forEach(gap => { gapsBySeq[gap.after_message_seq] = gap })

    const filteredMessages = messages.filter(msg => {
        const matchSearch = !search || msg.content?.toLowerCase().includes(search.toLowerCase())
            || msg.sender?.toLowerCase().includes(search.toLowerCase())
        const matchSender = filterSender === 'all' || msg.sender === filterSender
        const matchType =
            filterType === 'all' ||
            (filterType === 'deleted' && msg.is_deleted) ||
            (filterType === 'gap' && gapsBySeq[msg.sequence_number])
        return matchSearch && matchSender && matchType
    })

    const formatTime = (dateStr) => new Date(dateStr).toLocaleTimeString('id-ID', {
        hour: '2-digit', minute: '2-digit'
    })

    const formatDate = (dateStr) => new Date(dateStr).toLocaleDateString('id-ID', {
        day: 'numeric', month: 'short', year: 'numeric'
    })

    // Track last date shown to render date dividers
    let lastDate = null

    const handleExport = () => {
        const exportData = {
            session: {
                name: session.name,
                status: session.status,
                exported_at: new Date().toISOString(),
            },
            stats,
            gaps: gaps.map(gap => ({
                ...gap,
                inference: inferences[gap.id] || null,
            })),
            summary: {
                total_messages: stats?.total_messages,
                deleted_messages: stats?.deleted_messages,
                gaps_detected: gaps.length,
                high_priority_gaps: gaps.filter(g => g.suspicion_score >= 0.7).length,
                participants: Object.keys(stats?.participants || {}),
            }
        }

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `shadowtrace-${session.name?.replace(/\s+/g, '-')}-${Date.now()}.json`
        a.click()
        URL.revokeObjectURL(url)
        addToast?.('Hasil analisis berhasil diexport!', 'success')
    }

    return (
        <div>
            {/* Stats Bar */}
            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{stats.total_messages?.toLocaleString()}</div>
                        <div className="stat-label">Total Pesan</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--warning)' }}>
                            {gaps.length}
                        </div>
                        <div className="stat-label">Gap Terdeteksi</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--danger)' }}>
                            {stats.deleted_messages}
                        </div>
                        <div className="stat-label">Pesan Dihapus</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--danger)' }}>
                            {gaps.filter(g => g.suspicion_score >= 0.7).length}
                        </div>
                        <div className="stat-label">Gap Prioritas Tinggi</div>
                    </div>
                </div>
            )}

            {/* Toolbar */}
            <div className="toolbar">
                <div className="toolbar-left">
                    {session.status !== 'analyzed' ? (
                        <button
                            className="btn btn-primary"
                            onClick={() => onAnalyze(session.id)}
                            disabled={loading}
                        >
                            {loading ? (
                                <><span className="spinner-sm" /> Menganalisis...</>
                            ) : (
                                '🔍 Analisis Gap'
                            )}
                        </button>
                    ) : (
                        <button
                            className="btn btn-secondary"
                            onClick={() => onAnalyze(session.id)}
                            disabled={loading}
                        >
                            {loading ? '⟳ Menjalankan...' : '🔄 Analisis Ulang'}
                        </button>
                    )}

                    {gaps.length > 0 && (
                        <button className="btn btn-secondary" onClick={handleExport}>
                            ⬇ Export JSON
                        </button>
                    )}
                </div>

                <div className="toolbar-right">
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Cari pesan atau pengirim..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <select
                        className="sort-select"
                        value={filterSender}
                        onChange={(e) => setFilterSender(e.target.value)}
                    >
                        <option value="all">Semua pengirim</option>
                        {senders.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select
                        className="sort-select"
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                    >
                        <option value="all">Semua pesan</option>
                        <option value="deleted">Pesan dihapus</option>
                        <option value="gap">Hanya ada gap</option>
                    </select>
                </div>
            </div>

            {/* Filter result badge */}
            {(search || filterSender !== 'all' || filterType !== 'all') && (
                <div className="filter-badge">
                    Menampilkan {filteredMessages.length} dari {messages.length} pesan
                    <button className="filter-clear" onClick={() => {
                        setSearch(''); setFilterSender('all'); setFilterType('all')
                    }}>
                        ✕ Reset filter
                    </button>
                </div>
            )}

            {/* Main Content */}
            <div className="chat-container">
                {/* Messages Panel */}
                <div className="messages-panel">
                    {fetching ? (
                        <div className="loading">
                            <div className="spinner" /> Memuat pesan...
                        </div>
                    ) : filteredMessages.length === 0 ? (
                        <div className="loading">Tidak ada pesan yang cocok.</div>
                    ) : (
                        filteredMessages.map((msg) => {
                            const hasGapBefore = gapsBySeq[msg.sequence_number]
                            const dateStr = formatDate(msg.timestamp)
                            const showDate = dateStr !== lastDate
                            if (showDate) lastDate = dateStr

                            return (
                                <div key={msg.id}>
                                    {showDate && (
                                        <div className="date-divider">
                                            <span>{dateStr}</span>
                                        </div>
                                    )}
                                    {hasGapBefore && (
                                        <div className={`gap-indicator ${highlightedGap?.id === hasGapBefore.id ? 'gap-highlighted' : ''}`}>
                                            <span>⚠ Gap {Math.round(hasGapBefore.time_gap_seconds / 60)} menit</span>
                                            {hasGapBefore.expected_messages && (
                                                <span> · ~{hasGapBefore.expected_messages} pesan hilang</span>
                                            )}
                                            <span className={`gap-ind-score score-${hasGapBefore.suspicion_score >= 0.7 ? 'high' : hasGapBefore.suspicion_score >= 0.4 ? 'med' : 'low'}`}>
                                                {Math.round(hasGapBefore.suspicion_score * 100)}%
                                            </span>
                                        </div>
                                    )}
                                    <div className={`message ${msg.is_deleted ? 'deleted' : ''}`}>
                                        <div className="message-header">
                                            <span className="message-sender">{msg.sender}</span>
                                            <span className="message-time">{formatTime(msg.timestamp)}</span>
                                        </div>
                                        <div className="message-content">
                                            {msg.is_deleted
                                                ? '🚫 Pesan ini telah dihapus'
                                                : highlight(msg.content, search)
                                            }
                                        </div>
                                    </div>
                                </div>
                            )
                        })
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Gaps Sidebar */}
                <div className="sidebar-panel">
                    <div className="sidebar-header">
                        <h3>Gap Terdeteksi</h3>
                        {gaps.length > 0 && (
                            <span className="sidebar-count">{gaps.length}</span>
                        )}
                    </div>

                    {gaps.length === 0 ? (
                        <div className="sidebar-empty">
                            {session.status === 'analyzed'
                                ? '✅ Tidak ada gap mencurigakan'
                                : 'Jalankan analisis untuk mendeteksi gap'}
                        </div>
                    ) : (
                        <div className="gap-list">
                            {gaps
                                .sort((a, b) => b.suspicion_score - a.suspicion_score)
                                .map(gap => (
                                    <GapCard
                                        key={gap.id}
                                        gap={gap}
                                        inference={inferences[gap.id]}
                                        onHighlight={setHighlightedGap}
                                    />
                                ))
                            }
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

// Highlight search term in message content
function highlight(text, term) {
    if (!term || !text) return text
    const parts = text.split(new RegExp(`(${term})`, 'gi'))
    return parts.map((part, i) =>
        part.toLowerCase() === term.toLowerCase()
            ? <mark key={i} className="search-highlight">{part}</mark>
            : part
    )
}

export default ChatView

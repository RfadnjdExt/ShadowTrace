import { useState } from 'react'

function SessionList({ sessions, onSelect, onDelete, onRefresh }) {
    const [deleteConfirm, setDeleteConfirm] = useState(null)
    const [sortBy, setSortBy] = useState('date') // date | gaps | messages

    const formatDate = (dateStr) => {
        if (!dateStr) return '-'
        return new Date(dateStr).toLocaleDateString('id-ID', {
            day: 'numeric', month: 'short', year: 'numeric'
        })
    }

    const sorted = [...sessions].sort((a, b) => {
        if (sortBy === 'gaps') return (b.detected_gaps || 0) - (a.detected_gaps || 0)
        if (sortBy === 'messages') return (b.total_messages || 0) - (a.total_messages || 0)
        return new Date(b.created_at) - new Date(a.created_at)
    })

    if (sessions.length === 0) {
        return (
            <div className="card empty-state" style={{ marginTop: '1.5rem' }}>
                <div className="empty-icon">💬</div>
                <p className="empty-title">Belum ada session</p>
                <p className="empty-sub">Upload file export WhatsApp di atas untuk memulai.</p>
            </div>
        )
    }

    return (
        <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-header">
                <h2 className="card-title">Sessions ({sessions.length})</h2>
                <div className="header-actions">
                    <select
                        className="sort-select"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                    >
                        <option value="date">Terbaru</option>
                        <option value="gaps">Paling banyak gap</option>
                        <option value="messages">Paling banyak pesan</option>
                    </select>
                    <button className="btn btn-icon" onClick={onRefresh} title="Refresh">
                        ↻
                    </button>
                </div>
            </div>

            {sorted.map((session) => (
                <div key={session.id} className="session-item" onClick={() => onSelect(session)}>
                    <div className="session-info">
                        <h3>{session.name}</h3>
                        <div className="session-meta">
                            <span>{session.total_messages?.toLocaleString() || 0} pesan</span>
                            <span className="meta-dot">·</span>
                            <span>{formatDate(session.created_at)}</span>
                            {session.detected_gaps > 0 && (
                                <>
                                    <span className="meta-dot">·</span>
                                    <span style={{ color: 'var(--warning)' }}>
                                        {session.detected_gaps} gap
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="session-right" onClick={e => e.stopPropagation()}>
                        <span className={`session-status status-${session.status}`}>
                            {session.status}
                        </span>
                        {deleteConfirm === session.id ? (
                            <div className="delete-confirm">
                                <button
                                    className="btn btn-danger btn-xs"
                                    onClick={() => { onDelete(session.id); setDeleteConfirm(null) }}
                                >
                                    Hapus
                                </button>
                                <button
                                    className="btn btn-secondary btn-xs"
                                    onClick={() => setDeleteConfirm(null)}
                                >
                                    Batal
                                </button>
                            </div>
                        ) : (
                            <button
                                className="btn btn-icon btn-ghost"
                                onClick={() => setDeleteConfirm(session.id)}
                                title="Hapus session"
                            >
                                🗑
                            </button>
                        )}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default SessionList

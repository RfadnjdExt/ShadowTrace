function SessionList({ sessions, onSelect }) {
    if (sessions.length === 0) {
        return (
            <div className="card" style={{ marginTop: '1.5rem' }}>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No chat sessions yet. Upload a WhatsApp export to get started.
                </p>
            </div>
        )
    }

    const formatDate = (dateStr) => {
        if (!dateStr) return '-'
        return new Date(dateStr).toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        })
    }

    return (
        <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-header">
                <h2 className="card-title">Sessions ({sessions.length})</h2>
            </div>

            {sessions.map((session) => (
                <div
                    key={session.id}
                    className="session-item"
                    onClick={() => onSelect(session)}
                >
                    <div className="session-info">
                        <h3>{session.name}</h3>
                        <div className="session-meta">
                            {session.total_messages} messages | {formatDate(session.created_at)}
                            {session.detected_gaps > 0 && (
                                <span style={{ color: 'var(--warning)', marginLeft: '0.5rem' }}>
                                    {session.detected_gaps} gaps detected
                                </span>
                            )}
                        </div>
                    </div>
                    <span className={`session-status status-${session.status}`}>
                        {session.status}
                    </span>
                </div>
            ))}
        </div>
    )
}

export default SessionList

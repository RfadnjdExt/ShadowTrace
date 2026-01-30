function GapCard({ gap, inference }) {
    const getSuspicionLevel = (score) => {
        if (score >= 0.7) return 'high'
        if (score >= 0.4) return 'medium'
        return 'low'
    }

    const level = getSuspicionLevel(gap.suspicion_score)
    const reasons = gap.suspicion_reasons
        ? JSON.parse(gap.suspicion_reasons)
        : []

    return (
        <div className={`gap-card ${level === 'high' ? 'high-suspicion' : ''}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>
                    Seq {gap.before_message_seq} - {gap.after_message_seq}
                </span>
                <span style={{
                    fontSize: '0.75rem',
                    color: level === 'high' ? 'var(--danger)' :
                        level === 'medium' ? 'var(--warning)' : 'var(--success)'
                }}>
                    {Math.round(gap.suspicion_score * 100)}%
                </span>
            </div>

            <div className="suspicion-bar">
                <div
                    className={`suspicion-fill suspicion-${level}`}
                    style={{ width: `${gap.suspicion_score * 100}%` }}
                />
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {Math.round(gap.time_gap_seconds / 60)} min gap
                {gap.expected_messages && ` | ~${gap.expected_messages} missing`}
            </div>

            {reasons.length > 0 && (
                <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                    {reasons[0]}
                </div>
            )}

            {inference && (
                <div className="inference-box">
                    <div className="inference-label">AI Inference</div>
                    <div>{inference.predicted_intent}</div>
                    <div style={{
                        fontSize: '0.75rem',
                        color: 'var(--text-secondary)',
                        marginTop: '0.25rem'
                    }}>
                        Confidence: {Math.round(inference.confidence_score * 100)}%
                    </div>
                </div>
            )}
        </div>
    )
}

export default GapCard

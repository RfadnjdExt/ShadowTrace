import { useState } from 'react'

function GapCard({ gap, inference, onHighlight }) {
    const [expanded, setExpanded] = useState(false)

    const getSuspicionLevel = (score) => {
        if (score >= 0.7) return 'high'
        if (score >= 0.4) return 'medium'
        return 'low'
    }

    const level = getSuspicionLevel(gap.suspicion_score)
    const reasons = gap.suspicion_reasons
        ? (typeof gap.suspicion_reasons === 'string'
            ? JSON.parse(gap.suspicion_reasons)
            : gap.suspicion_reasons)
        : []

    const levelLabels = { high: 'TINGGI', medium: 'SEDANG', low: 'RENDAH' }
    const levelEmoji = { high: '🔴', medium: '🟡', low: '🟢' }

    const durationLabel = () => {
        const s = gap.time_gap_seconds
        if (s < 60) return `${s}d`
        if (s < 3600) return `${Math.round(s / 60)}m`
        return `${Math.round(s / 3600)}j`
    }

    return (
        <div
            className={`gap-card ${level === 'high' ? 'high-suspicion' : ''}`}
            onClick={() => { setExpanded(!expanded); onHighlight?.(gap) }}
        >
            {/* Header */}
            <div className="gap-card-header">
                <div className="gap-seq">
                    <span className="gap-seq-label">Seq</span>
                    <span>{gap.before_message_seq}–{gap.after_message_seq}</span>
                </div>
                <div className="gap-right">
                    <span className={`suspicion-badge suspicion-badge-${level}`}>
                        {levelEmoji[level]} {levelLabels[level]}
                    </span>
                    <span className="gap-score">{Math.round(gap.suspicion_score * 100)}%</span>
                </div>
            </div>

            {/* Bar */}
            <div className="suspicion-bar">
                <div
                    className={`suspicion-fill suspicion-${level}`}
                    style={{ width: `${gap.suspicion_score * 100}%` }}
                />
            </div>

            {/* Meta */}
            <div className="gap-meta">
                <span>⏱ {durationLabel()} gap</span>
                {gap.expected_messages && (
                    <span>📭 ~{gap.expected_messages} pesan hilang</span>
                )}
                <span className="gap-type-tag">{gap.detection_type?.replace(/_/g, ' ')}</span>
            </div>

            {/* Primary reason */}
            {reasons.length > 0 && (
                <div className="gap-reason">{reasons[0]}</div>
            )}

            {/* AI Inference (always visible) */}
            {inference && (
                <div className="inference-box">
                    <div className="inference-header">
                        <span className="inference-label">🤖 AI Inferensi</span>
                        <span className="inference-conf">
                            {Math.round(inference.confidence_score * 100)}% confidence
                        </span>
                    </div>
                    <div className="inference-intent">
                        {inference.predicted_intent || 'Tidak cukup bukti untuk prediksi.'}
                    </div>
                    {inference.predicted_sender && (
                        <div className="inference-sender">
                            Kemungkinan pengirim: <strong>{inference.predicted_sender}</strong>
                        </div>
                    )}
                    <div className="inference-model">{inference.model_used}</div>
                </div>
            )}

            {/* Expanded section */}
            {expanded && (
                <div className="gap-expanded">
                    {reasons.length > 1 && (
                        <div className="gap-reasons-all">
                            <div className="expanded-label">Semua alasan deteksi:</div>
                            {reasons.map((r, i) => (
                                <div key={i} className="gap-reason-item">• {r}</div>
                            ))}
                        </div>
                    )}
                    {inference?.reasoning && (
                        <div className="gap-reasoning">
                            <div className="expanded-label">Chain-of-thought AI:</div>
                            <p>{inference.reasoning}</p>
                        </div>
                    )}
                    {inference?.hallucination_flags?.length > 0 && (
                        <div className="gap-flags">
                            {inference.hallucination_flags.map((f, i) => (
                                <span key={i} className="flag-tag">{f}</span>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div className="gap-expand-hint">
                {expanded ? '▲ Sembunyikan detail' : '▼ Lihat detail'}
            </div>
        </div>
    )
}

export default GapCard

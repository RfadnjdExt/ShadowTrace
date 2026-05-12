import { useEffect } from 'react'

function Toast({ toast, onRemove }) {
    useEffect(() => {
        return () => {}
    }, [])

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠',
    }

    return (
        <div className={`toast toast-${toast.type}`} onClick={() => onRemove(toast.id)}>
            <span className="toast-icon">{icons[toast.type] || 'ℹ'}</span>
            <span className="toast-message">{toast.message}</span>
        </div>
    )
}

export default Toast

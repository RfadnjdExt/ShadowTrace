import { useState, useRef } from 'react'

function UploadZone({ onUpload, loading }) {
    const [dragover, setDragover] = useState(false)
    const [fileName, setFileName] = useState(null)
    const inputRef = useRef(null)

    const handleDrop = (e) => {
        e.preventDefault()
        setDragover(false)
        const file = e.dataTransfer.files[0]
        if (file && file.name.endsWith('.txt')) {
            setFileName(file.name)
            onUpload(file)
        } else if (file) {
            alert('Hanya file .txt dari WhatsApp yang didukung.')
        }
    }

    const handleChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            setFileName(file.name)
            onUpload(file)
        }
    }

    return (
        <div
            className={`upload-zone ${dragover ? 'dragover' : ''} ${loading ? 'loading-zone' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true) }}
            onDragLeave={() => setDragover(false)}
            onDrop={handleDrop}
            onClick={() => !loading && inputRef.current?.click()}
        >
            <input
                ref={inputRef}
                type="file"
                accept=".txt"
                onChange={handleChange}
                style={{ display: 'none' }}
            />

            {loading ? (
                <div className="upload-loading">
                    <div className="spinner-lg"></div>
                    <p className="upload-loading-text">Memproses file chat...</p>
                    {fileName && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            {fileName}
                        </p>
                    )}
                </div>
            ) : (
                <>
                    <div className="upload-icon-wrap">
                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17 8 12 3 7 8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                    </div>
                    <p className="upload-title">
                        {dragover ? 'Lepaskan file di sini' : 'Drop file WhatsApp atau klik untuk upload'}
                    </p>
                    <p className="upload-sub">
                        Format: <code>.txt</code> dari WhatsApp &gt; Export Chat
                    </p>
                </>
            )}
        </div>
    )
}

export default UploadZone

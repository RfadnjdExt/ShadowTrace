import { useState, useRef } from 'react'

function UploadZone({ onUpload, loading }) {
    const [dragover, setDragover] = useState(false)
    const inputRef = useRef(null)

    const handleDrop = (e) => {
        e.preventDefault()
        setDragover(false)

        const file = e.dataTransfer.files[0]
        if (file && file.name.endsWith('.txt')) {
            onUpload(file)
        }
    }

    const handleChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            onUpload(file)
        }
    }

    return (
        <div
            className={`upload-zone ${dragover ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true) }}
            onDragLeave={() => setDragover(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
        >
            <input
                ref={inputRef}
                type="file"
                accept=".txt"
                onChange={handleChange}
                style={{ display: 'none' }}
            />

            {loading ? (
                <div className="loading">
                    <div className="spinner"></div>
                    Processing...
                </div>
            ) : (
                <>
                    <div className="upload-icon">+</div>
                    <p>Drop WhatsApp export file here or click to upload</p>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                        Supports .txt files from WhatsApp export
                    </p>
                </>
            )}
        </div>
    )
}

export default UploadZone

import { useState, useRef } from 'react';

function UploadModal({ onClose, onUpload, progress, loading }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
    }
  };

  const handleUpload = () => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>📤 上传文档</h2>

        <div
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".docx,.txt"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          
          {file ? (
            <div className="file-selected">
              <span>📄 {file.name}</span>
              <span>{(file.size / 1024).toFixed(1)} KB</span>
            </div>
          ) : (
            <div className="upload-hint">
              <p>拖拽文件到此处，或点击选择</p>
              <p className="hint">支持 .docx, .txt 格式</p>
            </div>
          )}
        </div>

        {loading && (
          <div className="progress-bar">
            <div className="progress" style={{ width: `${progress}%` }}></div>
          </div>
        )}

        <div className="modal-actions">
          <button onClick={onClose} disabled={loading}>取消</button>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="primary"
          >
            {loading ? `上传中... ${progress}%` : '上传'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadModal;

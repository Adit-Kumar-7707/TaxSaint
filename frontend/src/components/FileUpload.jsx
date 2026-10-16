// TaxSaint file upload component for CSV / Excel statements
import React, { useState, useRef } from "react";
import { uploadStatement } from "../services/api";

function FileUpload({ userId, onUploadSuccess, disabled = false }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    setUploadStatus(null);
    const validExtensions = [".csv", ".xlsx", ".xls"];
    const hasValidExt = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );

    if (!hasValidExt) {
      setUploadStatus({
        type: "error",
        message: "Please select a valid CSV or Excel (.xlsx, .xls) statement."
      });
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    if (!userId) {
      setUploadStatus({
        type: "error",
        message: "No user selected. Please select or create a profile first."
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      const result = await uploadStatement(userId, selectedFile);
      setUploadStatus({
        type: "success",
        message: result.message || `Successfully imported ${result.imported || 0} records!`
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (typeof onUploadSuccess === "function") {
        onUploadSuccess(result);
      }
    } catch (err) {
      setUploadStatus({
        type: "error",
        message: err.message || "Failed to upload and process statement."
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".csv, .xlsx, .xls"
        style={{ display: "none" }}
        disabled={disabled || uploading}
      />

      <div
        className={`file-upload-zone ${isDragging ? "dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <div className="upload-icon">📄</div>
        <h4>Upload Statement or Transaction Batch</h4>
        <p>Drag and drop your bank or account statement (.csv, .xlsx), or click to browse</p>

        {selectedFile && (
          <div className="file-pill" onClick={(e) => e.stopPropagation()}>
            <span>📎 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {selectedFile && (
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem" }}>
          <button
            type="button"
            className="btn btn-accent"
            onClick={handleUpload}
            disabled={uploading || disabled}
          >
            {uploading ? "Processing Statement..." : "Process & Import Records"}
          </button>
        </div>
      )}

      {uploadStatus && (
        <div className={`taxsaint-banner ${uploadStatus.type}`} role="alert">
          <span>{uploadStatus.message}</span>
          <button type="button" onClick={() => setUploadStatus(null)}>✕</button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;

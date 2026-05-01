import React, { useState, useCallback, useRef } from "react";
import { uploadToLibrary } from "../api/client";

const ANOMALY_STATUS_OPTIONS = [
  "Not Sized - Approved",
  "Review Detection",
  "QC",
  "Needs Discovery",
  "Poor Data Quality",
  "Size Anomaly",
  "Approved",
];

const ANOMALY_TYPE_OPTIONS = [
  "Crack Like",
  "Metal Loss",
  "Weld",
  "Deformation",
  "Lamination",
  "Other",
];

const IDENTIFICATION_OPTIONS = {
  "Crack Like":  ["Crack", "Stress Corrosion Cracking", "Hook Crack", "EDM Notch", "Crack Cluster", "Lack of Fusion", "Weld Trim"],
  "Metal Loss":  ["Corrosion", "Corrosion Cluster", "Grinding", "Gouge", "Scratches", "Manufactured"],
  "Weld":        ["Girth Weld Anomaly", "Longitudinal Weld Anomaly", "Spiral Weld Anomaly", "Arc Strike", "Slag Inclusion"],
  "Deformation": ["Ovality", "Dent Plain", "Dent Kinked", "Dent Complex", "Dent Re-Rounded", "Ripple/Wrinkle", "Buckle", "Roof Topping"],
  "Lamination":  ["Planar Lamination", "Sloped Lamination", "Bulging Lamination", "Inclusion"],
  "Other":       ["Debris", "Artificial Anomaly", "Coating Disbondment", "Wall Thickness Increase", "Bubble", "Nominal Pipe"],
};

const WALL_LOCATION_OPTIONS = ["External", "Internal", "Mid-Wall", "N/A", "Through-Wall"];

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/tiff"];

const EMPTY_FORM = {
  anomaly_description: "",
  anomaly_status: "",
  anomaly_type: "",
  identification: "",
  wall_location: "",
  run_number: "",
  analysis_comment: "",
  analyst: "",
};

export default function LibraryUpload() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f) return;
    if (!ACCEPTED_TYPES.includes(f.type)) {
      setError("Please use a JPEG, PNG, or TIFF image.");
      return;
    }
    setFile(f);
    setError(null);
    setSuccess(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(f);
  }, []);

  const handleDragOver = useCallback((e) => { e.preventDefault(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setIsDragging(false); }, []);
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleFormChange = (field, value) => {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (field === "anomaly_type") next.identification = "";
      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadToLibrary(file, form);
      setSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setForm(EMPTY_FORM);
    setSuccess(null);
    setError(null);
  };

  if (success) {
    return (
      <div className="library-upload">
        <div className="upload-success">
          <div className="upload-success-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <p style={{ fontSize: "15px", fontWeight: 600 }}>Saved to Library</p>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            The image is now indexed and will appear in future search results.
          </p>
          {success.image.anomaly_type && (
            <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {success.image.anomaly_type}
              {success.image.identification ? ` — ${success.image.identification}` : ""}
            </p>
          )}
          <button className="btn btn-secondary" onClick={handleReset} style={{ marginTop: "8px" }}>
            Upload Another
          </button>
        </div>
      </div>
    );
  }

  const identificationOptions = form.anomaly_type ? IDENTIFICATION_OPTIONS[form.anomaly_type] || [] : [];

  return (
    <div className="library-upload">
      {/* Image drop zone */}
      <div
        className={`dropzone${isDragging ? " dropzone-active" : ""}`}
        style={{ marginTop: 0, minHeight: 180 }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current?.click()}
      >
        {preview ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
            <img src={preview} alt="Preview" className="dropzone-preview" />
            <button
              className="btn btn-secondary"
              style={{ fontSize: 12 }}
              onClick={(e) => { e.stopPropagation(); handleReset(); }}
            >
              Change Image
            </button>
          </div>
        ) : (
          <>
            <div className="dropzone-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
              </svg>
            </div>
            <p className="dropzone-text">Drop image or click to browse</p>
            <p className="dropzone-formats">JPEG, PNG, or TIFF</p>
          </>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.tiff,.tif"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Metadata form */}
      <form className="upload-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label className="form-label">Anomaly Description</label>
          <input
            className="form-input"
            type="text"
            placeholder="Describe the anomaly in one sentence"
            value={form.anomaly_description}
            onChange={(e) => handleFormChange("anomaly_description", e.target.value)}
          />
        </div>

        <div className="form-field">
          <label className="form-label">Anomaly Status</label>
          <select
            className="form-select"
            value={form.anomaly_status}
            onChange={(e) => handleFormChange("anomaly_status", e.target.value)}
          >
            <option value="">— Select Status —</option>
            {ANOMALY_STATUS_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label className="form-label">Anomaly Type</label>
          <select
            className="form-select"
            value={form.anomaly_type}
            onChange={(e) => handleFormChange("anomaly_type", e.target.value)}
          >
            <option value="">— Select Type —</option>
            {ANOMALY_TYPE_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label className="form-label">Identification</label>
          <select
            className="form-select"
            value={form.identification}
            disabled={!form.anomaly_type}
            onChange={(e) => handleFormChange("identification", e.target.value)}
          >
            <option value="">
              {form.anomaly_type ? "— Select Identification —" : "Select an Anomaly Type first"}
            </option>
            {identificationOptions.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label className="form-label">Wall Location</label>
          <select
            className="form-select"
            value={form.wall_location}
            onChange={(e) => handleFormChange("wall_location", e.target.value)}
          >
            <option value="">— Select Location —</option>
            {WALL_LOCATION_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label className="form-label">Run Number</label>
          <input
            className="form-input"
            type="text"
            placeholder="e.g. RUN-2024-001"
            value={form.run_number}
            onChange={(e) => handleFormChange("run_number", e.target.value)}
          />
        </div>

        <div className="form-field">
          <label className="form-label">Analysis Comment</label>
          <textarea
            className="form-textarea"
            placeholder="Any additional observations or notes about this image"
            value={form.analysis_comment}
            onChange={(e) => handleFormChange("analysis_comment", e.target.value)}
          />
        </div>

        <div className="form-field">
          <label className="form-label">Analyst</label>
          <input
            className="form-input"
            type="text"
            placeholder="Analyst name"
            value={form.analyst}
            onChange={(e) => handleFormChange("analyst", e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!file || uploading}
          style={{ alignSelf: "flex-end", minWidth: 140 }}
        >
          {uploading ? "Saving..." : "Save to Library"}
        </button>
      </form>
    </div>
  );
}

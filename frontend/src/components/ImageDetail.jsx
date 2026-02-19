import React, { useState } from "react";
import { getExplainability } from "../api/client";

export default function ImageDetail({ result, onBack }) {
  const { image, similarity_score, image_url } = result;
  const [heatmapUrl, setHeatmapUrl] = useState(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleToggleHeatmap = async () => {
    if (showHeatmap) {
      setShowHeatmap(false);
      return;
    }

    if (heatmapUrl) {
      setShowHeatmap(true);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const url = await getExplainability(image.id);
      setHeatmapUrl(url);
      setShowHeatmap(true);
    } catch (err) {
      setError("Failed to generate attention map");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="image-detail">
      <button className="btn btn-secondary" onClick={onBack}>
        Back to Results
      </button>

      <div className="detail-content">
        <div className="detail-image-container">
          <img
            src={showHeatmap && heatmapUrl ? heatmapUrl : image_url}
            alt={image.diagnosis || "Medical image"}
            className="detail-image"
          />
          <div className="heatmap-controls">
            <button
              className={`btn ${showHeatmap ? "btn-primary" : "btn-secondary"}`}
              onClick={handleToggleHeatmap}
              disabled={loading}
            >
              {loading ? "Generating..." : showHeatmap ? "Show Original" : "Show Attention Map"}
            </button>
            {error && <span className="heatmap-error">{error}</span>}
          </div>
        </div>

        <div className="detail-metadata">
          <h2>Image Details</h2>

          <div className="detail-score">
            <span className="detail-label">Similarity</span>
            <span className="detail-value">
              {(similarity_score * 100).toFixed(1)}%
            </span>
          </div>

          <table className="detail-table">
            <tbody>
              <DetailRow label="Diagnosis" value={image.diagnosis} />
              <DetailRow label="Classification" value={image.benign_malignant} />
              <DetailRow label="Tissue Type" value={image.tissue_type} />
              <DetailRow label="Age" value={image.age} />
              <DetailRow label="Sex" value={image.sex} />
              <DetailRow label="Dataset" value={image.dataset_source} />
              <DetailRow label="Image ID" value={image.id} />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <tr>
      <td className="detail-label">{label}</td>
      <td className="detail-value">{value || "N/A"}</td>
    </tr>
  );
}

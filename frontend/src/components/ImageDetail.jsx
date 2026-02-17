import React from "react";

export default function ImageDetail({ result, onBack }) {
  const { image, similarity_score, image_url } = result;

  return (
    <div className="image-detail">
      <button className="btn btn-secondary" onClick={onBack}>
        Back to Results
      </button>

      <div className="detail-content">
        <div className="detail-image-container">
          <img src={image_url} alt={image.diagnosis || "Medical image"} className="detail-image" />
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

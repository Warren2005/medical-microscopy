import React from "react";

export default function ResultsGrid({ results, onResultClick }) {
  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No similar images found. Try a different image or adjust filters.</p>
      </div>
    );
  }

  return (
    <div className="results-grid">
      {results.map((result, index) => (
        <div
          key={result.image.id}
          className="result-card"
          onClick={() => onResultClick(result)}
        >
          <div className="result-rank">#{index + 1}</div>
          <img
            src={result.image_url}
            alt={result.image.diagnosis || "Medical image"}
            className="result-image"
            loading="lazy"
          />
          <div className="result-info">
            <div className="result-score">
              {(result.similarity_score * 100).toFixed(1)}% match
            </div>
            {result.image.diagnosis && (
              <div className="result-diagnosis">{result.image.diagnosis}</div>
            )}
            {result.image.benign_malignant && (
              <span
                className={`badge ${
                  result.image.benign_malignant === "malignant"
                    ? "badge-malignant"
                    : "badge-benign"
                }`}
              >
                {result.image.benign_malignant}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

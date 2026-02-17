import React from "react";

export default function StatusBar({ health, results }) {
  const statusColor =
    health?.status === "healthy"
      ? "green"
      : health?.status === "degraded"
      ? "orange"
      : "red";

  const statusText =
    health?.status === "unreachable"
      ? "Backend Offline"
      : health?.status || "Checking...";

  return (
    <footer className="status-bar">
      <div className="status-item">
        <span className="status-dot" style={{ backgroundColor: statusColor }} />
        <span>{statusText}</span>
      </div>

      {results && (
        <>
          <div className="status-item">
            {results.result_count} result{results.result_count !== 1 ? "s" : ""}
          </div>
          <div className="status-item">
            Embed: {results.query_processing_time_ms.toFixed(0)}ms | Search:{" "}
            {results.search_time_ms.toFixed(0)}ms | Total:{" "}
            {results.total_time_ms.toFixed(0)}ms
          </div>
        </>
      )}
    </footer>
  );
}

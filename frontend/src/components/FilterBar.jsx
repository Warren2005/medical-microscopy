import React from "react";

export default function FilterBar({ options, filters, onChange }) {
  const handleChange = (field, value) => {
    onChange({ ...filters, [field]: value || undefined });
  };

  return (
    <div className="filter-bar">
      <span className="filter-label">Filters:</span>

      <select
        value={filters.diagnosis || ""}
        onChange={(e) => handleChange("diagnosis", e.target.value)}
      >
        <option value="">All Diagnoses</option>
        {options.diagnoses.map((d) => (
          <option key={d} value={d}>
            {d.replace(/_/g, " ")}
          </option>
        ))}
      </select>

      <select
        value={filters.tissue_type || ""}
        onChange={(e) => handleChange("tissue_type", e.target.value)}
      >
        <option value="">All Tissue Types</option>
        {options.tissue_types.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <select
        value={filters.benign_malignant || ""}
        onChange={(e) => handleChange("benign_malignant", e.target.value)}
      >
        <option value="">All Classifications</option>
        {options.benign_malignant.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </div>
  );
}

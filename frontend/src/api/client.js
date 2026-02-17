const BASE_URL = "http://localhost:8000/api/v1";

export async function searchSimilar(file, filters = {}) {
  const formData = new FormData();
  formData.append("file", file);

  const params = new URLSearchParams();
  if (filters.diagnosis) params.set("diagnosis", filters.diagnosis);
  if (filters.tissue_type) params.set("tissue_type", filters.tissue_type);
  if (filters.benign_malignant)
    params.set("benign_malignant", filters.benign_malignant);

  const queryString = params.toString();
  const url = `${BASE_URL}/search/similar${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, { method: "POST", body: formData });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error?.error?.message || `Search failed: ${response.status}`
    );
  }
  return response.json();
}

export async function getImageDetail(imageId) {
  const response = await fetch(`${BASE_URL}/images/${imageId}`);
  if (!response.ok) throw new Error(`Failed to fetch image: ${response.status}`);
  return response.json();
}

export async function getFilters() {
  const response = await fetch(`${BASE_URL}/images/filters`);
  if (!response.ok) throw new Error(`Failed to fetch filters: ${response.status}`);
  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

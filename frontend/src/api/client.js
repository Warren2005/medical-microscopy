// Auto-detect API URL: in browser (nginx proxy) use relative path, in Electron use localhost
const isElectron = typeof window !== "undefined" && window.process && window.process.type;
const BASE_URL = isElectron ? "http://localhost:8000/api/v1" : "/api/v1";

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

export async function searchByText(query, filters = {}) {
  const body = { query };
  if (filters.diagnosis) body.diagnosis = filters.diagnosis;
  if (filters.tissue_type) body.tissue_type = filters.tissue_type;
  if (filters.benign_malignant) body.benign_malignant = filters.benign_malignant;

  const response = await fetch(`${BASE_URL}/search/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error?.error?.message || `Text search failed: ${response.status}`
    );
  }
  return response.json();
}

export async function submitFeedback(queryImageId, resultImageId, vote) {
  const response = await fetch(`${BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query_image_id: queryImageId,
      result_image_id: resultImageId,
      vote,
    }),
  });
  if (!response.ok) throw new Error(`Feedback failed: ${response.status}`);
  return response.json();
}

export function createSearchWebSocket(onMessage, onError) {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsHost = isElectron ? "localhost:8000" : window.location.host;
  const ws = new WebSocket(`${wsProtocol}//${wsHost}/api/v1/ws/search`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  ws.onerror = (err) => {
    if (onError) onError(err);
  };

  return ws;
}

export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

export async function getExplainability(imageId) {
  const response = await fetch(`${BASE_URL}/explain?image_id=${imageId}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Explain failed: ${response.status}`);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function analyzesite(payload) {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json();
}

export async function getSupportedStates() {
  const res = await fetch(`${API_BASE}/api/v1/states`);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json();
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json();
}

export function startResearch(question) {
  return request("/api/research/start", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function resumeResearch(threadId, approved) {
  return request("/api/research/resume", {
    method: "POST",
    body: JSON.stringify({
      thread_id: threadId,
      approved,
    }),
  });
}

export function getResearchHistory() {
  return request("/api/research/history");
}

export function getResearchDetail(threadId) {
  return request(`/api/research/history/${threadId}`);
}
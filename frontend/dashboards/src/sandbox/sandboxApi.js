const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

function apiUrl(path) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export async function resolveSandboxInvite(inviteId) {
  if (!inviteId) return null;
  const response = await fetch(apiUrl(`/api/v1/sandbox/invites/${encodeURIComponent(inviteId)}/`));
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Invite resolution failed (${response.status})`);
  }
  return response.json();
}

export async function createSandboxSession({ inviteId, role, school, track, guidance, tour }) {
  const response = await fetch(apiUrl("/api/v1/sandbox/session/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      invite_id: inviteId || null,
      role,
      school,
      track,
      guidance,
      tour,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Sandbox launch failed (${response.status})`);
  }

  return response.json();
}

export function storeSandboxSession(session) {
  sessionStorage.setItem("crown.jwt.access", session.access);
  sessionStorage.setItem("crown.jwt.refresh", session.refresh || "");
  sessionStorage.setItem("crown.school.id", session.school_id);
  sessionStorage.setItem("crown.school.name", session.school_name || "");
  sessionStorage.setItem("crown.role", session.role);
  sessionStorage.setItem("crown.sandbox.command_center", JSON.stringify(session.command_center || {}));

  localStorage.setItem("crown.role", session.role);
  localStorage.setItem("crown.demo.role", session.role);
  localStorage.setItem("crown.demo.school_id", session.school_id);
  localStorage.setItem("crown.demo.guidance", session.guidance || "guided");
  localStorage.setItem("crown.demo.tour", session.tour || "");
}

export async function recordSandboxEvent(payload) {
  try {
    await fetch(apiUrl("/api/v1/sandbox/events/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  } catch {
    // Telemetry must never block the buyer experience.
  }
}

export async function submitSandboxFeedback(payload) {
  const response = await fetch(apiUrl("/api/v1/sandbox/feedback/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Feedback failed (${response.status})`);
  }

  return response.json();
}

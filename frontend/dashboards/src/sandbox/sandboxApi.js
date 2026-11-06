import { authenticatedJson } from "../utils/authClient";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

function apiUrl(path) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export async function resolveSandboxInvite(inviteId) {
  if (!inviteId) return null;
  const response = await globalThis.fetch(apiUrl(`/api/v1/sandbox/invites/${encodeURIComponent(inviteId)}/`));
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Invite resolution failed (${response.status})`);
  }
  return response.json();
}

function sameOriginSandboxCsrfHeaders(url) {
  // A first session mints a Django session and sets the CSRF cookie. The next
  // role switch is an authenticated session POST and must pass the normal
  // CSRF guard. Do not send tokens to arbitrary cross-origin API hosts.
  const headers = { "Content-Type": "application/json" };
  if (typeof document === "undefined" || typeof location === "undefined") return headers;
  const target = new URL(url, location.href);
  if (target.origin !== location.origin) return headers;
  const cookie = document.cookie.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken="));
  if (cookie) {
    try {
      headers["X-CSRFToken"] = decodeURIComponent(cookie.slice("csrftoken=".length));
    } catch {
      // Malformed cookie: let the server reject the protected operation.
    }
  }
  return headers;
}

export async function createSandboxSession({ inviteId, role, school, track, guidance, tour }) {
  const url = apiUrl("/api/v1/sandbox/session/");
  const response = await globalThis.fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: sameOriginSandboxCsrfHeaders(url),
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
    await authenticatedJson("/api/v1/sandbox/events/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  } catch {
    // Telemetry must never block the buyer experience.
  }
}

export async function submitSandboxFeedback(payload) {
  const response = await globalThis.fetch(apiUrl("/api/v1/sandbox/feedback/"), {
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

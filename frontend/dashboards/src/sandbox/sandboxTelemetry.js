const STORAGE_KEY = "crown.sandbox.telemetry";
const MAX_BUFFERED_EVENTS = 100;

function normalizePayload(payload = {}) {
  return {
    track: payload.track || "unknown",
    guidance: payload.guidance || "unknown",
    persona: payload.persona || "unknown",
    school: payload.school || "unknown",
    tour: payload.tour || "unknown",
    step: payload.step || null,
  };
}

function readBufferedEvents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeBufferedEvents(events) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(-MAX_BUFFERED_EVENTS)));
  } catch {
    // Telemetry must never break the sandbox experience.
  }
}

export function recordSandboxEvent(eventName, payload = {}) {
  const event = {
    event: eventName,
    ...normalizePayload(payload),
    occurred_at: new Date().toISOString(),
  };

  const buffered = readBufferedEvents();
  buffered.push(event);
  writeBufferedEvents(buffered);

  if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
    try {
      const body = new Blob([JSON.stringify(event)], { type: "application/json" });
      navigator.sendBeacon("/api/v1/sandbox/events/", body);
      return event;
    } catch {
      return event;
    }
  }

  return event;
}

export function getBufferedSandboxEvents() {
  return readBufferedEvents();
}

export function clearBufferedSandboxEvents() {
  writeBufferedEvents([]);
}

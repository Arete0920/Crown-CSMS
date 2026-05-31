const STORAGE_KEY = "crown_admissions_lifecycle_state";

function getStorage() {
  if (typeof globalThis === "undefined") {
    return null;
  }

  try {
    return globalThis.localStorage || null;
  } catch {
    return null;
  }
}

function writeLifecycleState(stage, details) {
  const storage = getStorage();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        stage,
        details: details && typeof details === "object" ? details : {},
        recordedAt: new Date().toISOString(),
      }),
    );
  } catch {
    // Ignore storage errors in browser privacy modes or test sandboxes.
  }
}

export function markAdmissionsLifecycleStarted(source) {
  writeLifecycleState("started", { source: String(source || "").trim() });
}

export function markAdmissionsLifecycleSubmitted(details) {
  writeLifecycleState("submitted", details);
}

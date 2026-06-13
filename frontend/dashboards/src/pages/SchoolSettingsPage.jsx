import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const SCHOOL_API = "/api/v1/school/";

function normalizeError(error) {
  if (!error) return "Unknown error.";
  if (typeof error.body === "string" && error.body.trim()) return error.body;
  if (error.body?.detail) return String(error.body.detail);
  if (error.body && typeof error.body === "object") {
    try {
      return JSON.stringify(error.body);
    } catch {
      return String(error.body);
    }
  }
  if (typeof error.message === "string" && error.message.trim()) return error.message;
  return "Request failed.";
}

export default function SchoolSettingsPage() {
  const [form, setForm] = useState({ name: "", timezone: "", is_active: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;

    apiFetch(SCHOOL_API)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        if (!active) return;
        setForm({
          name: data.name || "",
          timezone: data.timezone || "",
          is_active: Boolean(data.is_active),
        });
      })
      .catch((nextError) => {
        if (!active) return;
        setError(normalizeError(nextError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const hasRequiredFields = useMemo(
    () => Boolean(form.name.trim()) && Boolean(form.timezone.trim()),
    [form]
  );

  function handleChange(field) {
    return (event) => {
      const value = field === "is_active" ? event.target.checked : event.target.value;
      setSuccess("");
      setError("");
      setForm((current) => ({ ...current, [field]: value }));
    };
  }

  async function handleSave(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const response = await apiFetch(SCHOOL_API, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          timezone: form.timezone,
          is_active: form.is_active,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      setForm({
        name: data.name || "",
        timezone: data.timezone || "",
        is_active: Boolean(data.is_active),
      });
      setSuccess("School settings saved.");
    } catch (nextError) {
      setError(normalizeError(nextError));
    } finally {
      setSaving(false);
    }
  }

  return (
    <CrownLayout
      title="School Settings"
      subtitle="Authoritative school identity and timezone configuration"
    >
      <form onSubmit={handleSave} style={{ display: "grid", gap: 16, maxWidth: 720 }}>
        {loading ? <div aria-live="polite">Loading school settings…</div> : null}
        {error ? (
          <div role="alert" style={{ color: "var(--crown-danger)" }}>
            {error}
          </div>
        ) : null}
        {success ? (
          <output aria-live="polite" style={{ color: "var(--crown-ok)" }}>
            {success}
          </output>
        ) : null}

        <label style={{ display: "grid", gap: 6 }}>
          <span>School name</span>
          <input value={form.name} onChange={handleChange("name")} disabled={loading || saving} />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Timezone</span>
          <input value={form.timezone} onChange={handleChange("timezone")} disabled={loading || saving} />
        </label>

        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={handleChange("is_active")}
            disabled={loading || saving}
          />
          <span>School is active</span>
        </label>

        <div>
          <button type="submit" disabled={loading || saving || !hasRequiredFields}>
            {saving ? "Saving…" : "Save settings"}
          </button>
        </div>
      </form>
    </CrownLayout>
  );
}

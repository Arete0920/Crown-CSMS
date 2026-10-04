import { useCallback, useEffect, useState } from "react";
import { crownApiClient } from "../../api/client";

const BASE = "/api/comms/";
const INITIAL = { title: "Re-enrollment information", blocks: [{ type: "action", title: "Plan for the coming school year", body: "Review the re-enrollment instructions and tell us your family's plans.", link: "/parent" }], publish_at: "", expires_at: "" };

async function api(path, data) {
  const response = await crownApiClient.request({ url: BASE + path, method: data === undefined ? "GET" : "POST", data });
  return response.data;
}
async function list(path) {
  const data = await api(path);
  if (!Array.isArray(data)) throw new Error("School notices are temporarily unavailable. Please try again.");
  return data;
}
function errorText(error) {
  const detail = error.response?.data?.detail || error.response?.data || error.message;
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}
function ContentPreview({ content }) {
  return <div className="crown-card" style={{ padding: 16 }}>
    <h3>{content.title}</h3><p>{content.school} · {content.year}</p>
    <p>Re-enrollment deadline: <strong>{content.deadline}</strong></p>
    {content.blocks.map((block, index) => <section key={index}>
      <h4>{block.title}</h4><p style={{ whiteSpace: "pre-wrap" }}>{block.body}</p>
      {block.link && <a href={block.link}>View details</a>}
    </section>)}
    {content.resources?.map((resource) => <p key={resource.slug}>Resource: {resource.title} · revision {resource.updated_at}</p>)}
  </div>;
}

export function ContentReleaseWorkbench({ sessionId }) {
  const [releases, setReleases] = useState([]);
  const [deadline, setDeadline] = useState("");
  const [zone, setZone] = useState("America/New_York");
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState(INITIAL);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = useCallback(async () => {
    if (sessionId) setReleases(await list(`releases/session/${sessionId}/`));
  }, [sessionId]);
  useEffect(() => {
    let active = true;
    setSelected(null); setPreview(null); setForm(INITIAL); setReleases([]);
    if (sessionId) list(`releases/session/${sessionId}/`).then((data) => { if (active) setReleases(data); }).catch((e) => { if (active) setError(errorText(e)); });
    return () => { active = false; };
  }, [sessionId]);
  if (!sessionId) return null;
  function edit(key, value) { setForm((current) => ({ ...current, [key]: value })); setPreview(null); }
  function choose(release) {
    setSelected(release); setPreview(null); setError("");
    setForm({ title: release.title, blocks: release.blocks, publish_at: release.publish_at || "", expires_at: release.expires_at || "" });
  }
  async function run(action) {
    setBusy(true); setError("");
    try {
      let result;
      const content = { ...form, publish_at: form.publish_at || null, expires_at: form.expires_at || null };
      if (action === "deadline") {
        await api(`releases/session/${sessionId}/deadline/`, { deadline_at: deadline, communication_timezone: zone });
        setPreview(null);
      } else if (action === "save") {
        result = selected ? await api(`releases/${selected.id}/update/`, { revision: selected.revision, content }) : await api(`releases/session/${sessionId}/`, content);
        setSelected(result); setPreview(null);
      } else if (action === "correction") {
        result = await api(`releases/session/${sessionId}/`, { ...content, supersedes: selected.id });
        setSelected(result); setPreview(null);
      } else if (action === "preview") {
        setPreview(await api(`releases/${selected.id}/preview/`, {}));
      } else {
        result = await api(`releases/${selected.id}/${action}/`, { revision: selected.revision, fingerprint: preview?.fingerprint });
        setSelected(result);
      }
      await refresh();
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  const immutable = selected && ["published", "cancelled"].includes(selected.status);
  return <section className="crown-card" style={{ padding: 20, marginTop: 20 }} aria-label="Re-enrollment communications">
    <h2>Re-enrollment communications</h2>
    <p>Year and deadline come from the re-enrollment configuration. Save changes before previewing.</p>
    <label>Update authoritative deadline<input value={deadline} placeholder="2027-03-01T17:00:00-05:00" onChange={(e) => setDeadline(e.target.value)} /></label>
    <label>School timezone<input value={zone} onChange={(e) => setZone(e.target.value)} /></label>
    <button type="button" disabled={busy || !deadline} onClick={() => run("deadline")}>Save deadline</button>
    <p>After a deadline change, preview and approve a draft again. Published notices require a correction release.</p>
    <button type="button" className="crown-btn" onClick={() => { setSelected(null); setForm(INITIAL); setPreview(null); }}>New release</button>
    <button type="button" className="crown-btn" disabled={busy} onClick={() => refresh().catch((e) => setError(errorText(e)))}>Refresh status</button>
    <ul>{releases.map((r) => <li key={r.id}><button type="button" disabled={busy} onClick={() => choose(r)}>{r.title} · {r.status} · version {r.revision}</button>{r.last_error && <p role="alert">{r.last_error}</p>}</li>)}</ul>
    <fieldset disabled={busy || immutable}>
      <label>Release title<input className="crown-input" value={form.title} onChange={(e) => edit("title", e.target.value)} maxLength={200} /></label>
      {form.blocks.map((block, index) => <fieldset key={index}>
        <legend>Content block {index + 1}</legend>
        {[["type", "Block type"], ["title", "Heading"], ["body", "Instructions"], ["link", "Link"], ["resource_slug", "Public Solomon resource slug (optional)"]].map(([key, label]) => <label key={key}>{label}
          {key === "type" ? <select value={block.type} onChange={(e) => edit("blocks", form.blocks.map((b, i) => i === index ? { ...b, type: e.target.value } : b))}>{["announcement", "event", "permission", "lesson", "action"].map((type) => <option key={type}>{type}</option>)}</select>
            : key === "body" ? <textarea value={block.body} onChange={(e) => edit("blocks", form.blocks.map((b, i) => i === index ? { ...b, body: e.target.value } : b))} />
              : <input value={block[key] || ""} onChange={(e) => edit("blocks", form.blocks.map((b, i) => i === index ? { ...b, [key]: e.target.value } : b))} />}
        </label>)}
        <button type="button" onClick={() => edit("blocks", form.blocks.filter((_, i) => i !== index))} disabled={form.blocks.length === 1}>Remove block</button>
      </fieldset>)}
      <button type="button" disabled={form.blocks.length >= 12} onClick={() => edit("blocks", [...form.blocks, { type: "announcement", title: "", body: "" }])}>Add block</button>
      <label>Publish at (ISO time with offset; blank means manual)<input value={form.publish_at} placeholder="2027-02-01T08:00:00-05:00" onChange={(e) => edit("publish_at", e.target.value)} /></label>
      <label>Expires at (ISO time with offset; optional)<input value={form.expires_at} onChange={(e) => edit("expires_at", e.target.value)} /></label>
      <button type="button" className="crown-btn crown-btn-primary" onClick={() => run("save")}>Save draft</button>
    </fieldset>
    {selected && <div>
      <p>Status: {selected.status} · version {selected.revision}</p>
      <button type="button" disabled={busy || immutable} onClick={() => run("preview")}>Preview saved release</button>
      <button type="button" disabled={busy || immutable || !preview} onClick={() => run("approve")}>Approve preview and schedule</button>
      <button type="button" disabled={busy || selected.status !== "approved"} onClick={() => run("publish")}>Publish now</button>
      <button type="button" disabled={busy || immutable} onClick={() => run("cancel")}>Cancel release</button>
      {selected.status === "published" && <button type="button" disabled={busy} onClick={() => run("correction")}>Create correction draft</button>}
      <p>Recipients: {selected.metrics.recipients}; email accepted: {selected.metrics.email_accepted}; pending: {selected.metrics.email_pending}; failed permanently: {selected.metrics.email_dead}; attempts: {selected.metrics.attempts}; acknowledged: {selected.metrics.acknowledged}</p>
      {selected.metrics.email_errors?.map((failure) => <p role="alert" key={failure.receipt_id}>Email {failure.state.toLowerCase()}, attempt {failure.attempts}: {failure.error}</p>)}
      <p>Family intent: returning {selected.metrics.responses.returning}, declining {selected.metrics.responses.declining}, undecided {selected.metrics.responses.undecided}.</p>
      <p>Email acceptance and family intent do not confirm delivery, payment, or completed enrollment.</p>
    </div>}
    {preview && <><p>Preview audience: {preview.recipients} guardians · {preview.email_recipients} emails · {preview.portal_recipients} portal accounts</p><ContentPreview content={preview} /></>}
    {error && <p role="alert">{error}</p>}
  </section>;
}

export function FamilyReleaseFeed() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = useCallback(async () => { setItems(await list("family-releases/")); }, []);
  useEffect(() => { refresh().catch((e) => setError(errorText(e))); }, [refresh]);
  async function respond(id, response) {
    setBusy(true); setError("");
    try { await api(`family-releases/${id}/respond/`, { response }); await refresh(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <section aria-label="School re-enrollment notices" className="crown-card" style={{ padding: 20 }}>
    <h2>School re-enrollment notices</h2>
    {items.length === 0 && !error && <p>No current re-enrollment notices.</p>}
    {items.map((item) => <article key={item.id}>
      <ContentPreview content={item} />
      <p>Your plans: {item.response || "No response recorded"}. This response does not complete enrollment.</p>
      {["returning", "declining", "undecided"].map((response) => <button key={response} type="button" className="crown-btn" disabled={busy} onClick={() => respond(item.id, response)}>{response}</button>)}
    </article>)}
    {error && <p role="alert">{error}</p>}
  </section>;
}

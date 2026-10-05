import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";

async function api(path, opts = {}) {
  const response = await apiFetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...opts.headers,
    },
  });
  const text = await response.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }
  if (!response.ok) {
    const detail = payload && typeof payload === "object" ? payload.detail : payload;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || `Request failed (${response.status})`));
  }
  return payload;
}

export default function MyElectronicFormsPage() {
  const [envelopes, setEnvelopes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [disclosure, setDisclosure] = useState(null);
  const [signedName, setSignedName] = useState("");
  const [ack, setAck] = useState(false);
  const [intent, setIntent] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const signerStatus = selected?.current_signer?.status || "";

  async function loadList() {
    const rows = await api("/api/v1/forms/envelopes/my/");
    setEnvelopes(Array.isArray(rows) ? rows : []);
  }

  async function loadEnvelope(id) {
    setErr("");
    const row = await api(`/api/v1/forms/envelopes/${id}/`);
    setSelected(row);
    setSignedName(row?.current_signer?.display_name || "");
    setAck(false);
    setIntent(false);
  }

  useEffect(() => {
    Promise.all([
      loadList(),
      api("/api/v1/forms/consent-disclosure/").then(setDisclosure),
    ]).catch((error) => setErr(String(error.message || error)));
  }, []);

  const snapshotText = useMemo(() => {
    if (!selected?.document_snapshot) return "";
    const template = selected.document_snapshot.template || {};
    const data = selected.document_snapshot.data || {};
    return [
      template.title || selected.title,
      template.body || "",
      "",
      "Record data:",
      JSON.stringify(data, null, 2),
    ].join("\n");
  }, [selected]);

  async function consent() {
    if (!selected || !disclosure) return;
    setBusy(true);
    setErr("");
    try {
      await api(`/api/v1/forms/envelopes/${selected.id}/consent/`, {
        method: "POST",
        body: JSON.stringify({
          disclosure_version: disclosure.version,
          hardware_software_ack: ack,
        }),
      });
      await loadEnvelope(selected.id);
      await loadList();
    } catch (error) {
      setErr(String(error.message || error));
    } finally {
      setBusy(false);
    }
  }

  async function sign() {
    if (!selected) return;
    setBusy(true);
    setErr("");
    try {
      await api(`/api/v1/forms/envelopes/${selected.id}/sign/`, {
        method: "POST",
        body: JSON.stringify({
          signed_name: signedName,
          intent_to_sign: intent,
        }),
      });
      await loadEnvelope(selected.id);
      await loadList();
    } catch (error) {
      setErr(String(error.message || error));
    } finally {
      setBusy(false);
    }
  }

  async function paperCopy() {
    if (!selected) return;
    setBusy(true);
    setErr("");
    try {
      await api(`/api/v1/forms/envelopes/${selected.id}/paper-copy/`, { method: "POST", body: "{}" });
      await loadEnvelope(selected.id);
      await loadList();
    } catch (error) {
      setErr(String(error.message || error));
    } finally {
      setBusy(false);
    }
  }

  async function withdraw() {
    if (!selected) return;
    setBusy(true);
    setErr("");
    try {
      await api(`/api/v1/forms/envelopes/${selected.id}/withdraw-consent/`, { method: "POST", body: "{}" });
      await loadEnvelope(selected.id);
      await loadList();
    } catch (error) {
      setErr(String(error.message || error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <CrownLayout
      title="My Forms & Signatures"
      subtitle="Review, retain, consent to, and sign records assigned to you."
    >
      {err ? <ErrorBanner title="Forms unavailable" message={err} /> : null}

      <div style={{ display: "grid", gridTemplateColumns: "minmax(240px, 0.8fr) minmax(0, 2fr)", gap: 16 }}>
        <div className="crown-card">
          <h2 style={{ marginTop: 0 }}>Assigned forms</h2>
          <div style={{ display: "grid", gap: 8 }}>
            {envelopes.map((row) => (
              <button
                key={row.id}
                type="button"
                className="crown-btn"
                onClick={() => loadEnvelope(row.id).catch((error) => setErr(String(error.message || error)))}
                style={{ textAlign: "left" }}
              >
                <div style={{ fontWeight: 700 }}>{row.title}</div>
                <div style={{ fontSize: 12 }}>
                  {row.current_signer?.status || row.status} · {row.document_sha256?.slice(0, 12)}…
                </div>
              </button>
            ))}
            {envelopes.length === 0 ? <div>No forms are currently assigned to you.</div> : null}
          </div>
        </div>

        <div className="crown-card">
          {!selected ? (
            <div>Select a form to review its exact retained record.</div>
          ) : (
            <>
              <h2 style={{ marginTop: 0 }}>{selected.title}</h2>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 12 }}>
                Document SHA-256: <code>{selected.document_sha256}</code>
              </div>

              <pre style={{ whiteSpace: "pre-wrap", border: "1px solid var(--crown-border)", borderRadius: 8, padding: 12, maxHeight: 360, overflow: "auto" }}>
                {snapshotText}
              </pre>

              {signerStatus !== "SIGNED" ? (
                <>
                  <div style={{ marginTop: 16 }}>
                    <h3>Electronic record consent</h3>
                    <p>{disclosure?.text}</p>
                    <p style={{ fontSize: 12, color: "var(--crown-muted)" }}>
                      Requirements: {disclosure?.hardware_software_requirements} Paper copy fee: $<span>{disclosure?.paper_copy_fee || "0.00"}</span>.
                    </p>
                  </div>

                  {signerStatus !== "CONSENTED" ? (
                    <>
                      <label style={{ display: "block", marginTop: 10 }}>
                        <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />{" "}
                        I can access, save, or print this electronic record.
                      </label>
                      <button className="crown-btn" type="button" disabled={busy || !ack} onClick={consent} style={{ marginTop: 10 }}>
                        Consent to electronic records
                      </button>
                    </>
                  ) : (
                    <>
                      <label style={{ display: "block", marginTop: 14 }}>
                        Typed signature
                        <input value={signedName} onChange={(e) => setSignedName(e.target.value)} />
                      </label>
                      <label style={{ display: "block", marginTop: 10 }}>
                        <input type="checkbox" checked={intent} onChange={(e) => setIntent(e.target.checked)} />{" "}
                        I intend to sign and adopt this exact record.
                      </label>
                      <button className="crown-btn" type="button" disabled={busy || !signedName.trim() || !intent} onClick={sign} style={{ marginTop: 10 }}>
                        Sign this record
                      </button>
                    </>
                  )}

                  <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
                    <button className="crown-btn" type="button" disabled={busy} onClick={paperCopy}>Request paper copy</button>
                    {signerStatus === "CONSENTED" ? (
                      <button className="crown-btn" type="button" disabled={busy} onClick={withdraw}>Withdraw electronic consent</button>
                    ) : null}
                  </div>
                </>
              ) : (
                <div style={{ marginTop: 16, fontWeight: 700 }}>
                  Signed {selected.current_signer?.signed_at ? new Date(selected.current_signer.signed_at).toLocaleString() : ""}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </CrownLayout>
  );
}

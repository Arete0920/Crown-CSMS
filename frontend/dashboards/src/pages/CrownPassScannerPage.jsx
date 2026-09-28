import { useEffect, useRef, useState } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

function authHeaders() {
  const token = sessionStorage.getItem("crown.jwt.access") || "";
  const schoolId = sessionStorage.getItem("crown.school.id") || "";
  const headers = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (schoolId) headers["X-School-Id"] = schoolId;
  return headers;
}

export default function CrownPassScannerPage() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const scanTimerRef = useRef(null);
  const [credential, setCredential] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cameraStatus, setCameraStatus] = useState("idle");

  async function redeem(value) {
    const token = (value || "").trim();
    if (!token || busy) return;
    setBusy(true);
    setResult(null);
    try {
      const response = await globalThis.fetch(`${apiBase()}/api/v1/crownpass/redeem/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ credential: token }),
      });
      const payload = await response.json();
      setResult({
        ok: response.ok,
        result: payload?.result || "invalid",
        reason: payload?.reason || "",
        ticketId: payload?.ticket_id || "",
      });
      if (response.ok) setCredential("");
    } catch (err) {
      setResult({ ok: false, result: "error", reason: String(err?.message || err) });
    } finally {
      setBusy(false);
    }
  }

  async function startCamera() {
    if (!("BarcodeDetector" in globalThis)) {
      setCameraStatus("unsupported");
      return;
    }
    try {
      detectorRef.current = new globalThis.BarcodeDetector({ formats: ["qr_code"] });
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      videoRef.current.srcObject = streamRef.current;
      await videoRef.current.play();
      setCameraStatus("scanning");

      const scanFrame = async () => {
        try {
          if (detectorRef.current && videoRef.current && !busy) {
            const codes = await detectorRef.current.detect(videoRef.current);
            if (codes.length && codes[0].rawValue) {
              await redeem(codes[0].rawValue);
            }
          }
        } catch {
          setCameraStatus("error");
        }
        scanTimerRef.current = globalThis.setTimeout(scanFrame, 500);
      };
      scanFrame();
    } catch {
      setCameraStatus("error");
    }
  }

  function stopCamera() {
    if (scanTimerRef.current) globalThis.clearTimeout(scanTimerRef.current);
    scanTimerRef.current = null;
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) track.stop();
    }
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraStatus("idle");
  }

  useEffect(() => stopCamera, []);

  const label =
    result?.result === "accepted" ? "Accepted" :
    result?.result === "duplicate" ? "Already used" :
    result?.result === "invalid" ? "Invalid ticket" :
    result?.result === "error" ? "Scanner error" : "";

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem" }}>
      <header>
        <p style={{ margin: 0, fontWeight: 700 }}>CROWNPASS</p>
        <h1>Gate Scanner</h1>
      </header>

      {result && (
        <section role="status" style={{ border: "2px solid currentColor", borderRadius: 12, padding: 18, marginBottom: 18 }}>
          <strong style={{ fontSize: "1.3rem" }}>{label}</strong>
          {result.ticketId && <div>Ticket {result.ticketId}</div>}
          {result.reason && <div>{result.reason}</div>}
        </section>
      )}

      <section style={{ marginBottom: 20 }}>
        <video ref={videoRef} playsInline muted style={{ width: "100%", maxHeight: 360, background: "#111", borderRadius: 12 }} />
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          {cameraStatus !== "scanning" ? (
            <button type="button" onClick={startCamera}>Start Camera Scanner</button>
          ) : (
            <button type="button" onClick={stopCamera}>Stop Camera</button>
          )}
        </div>
        {cameraStatus === "unsupported" && (
          <p>This browser does not support built-in QR detection. Use manual entry below.</p>
        )}
        {cameraStatus === "error" && (
          <p>Camera scanning is unavailable. Use manual entry below.</p>
        )}
      </section>

      <form onSubmit={(event) => { event.preventDefault(); redeem(credential); }}>
        <label htmlFor="crownpass-credential"><strong>Manual credential</strong></label>
        <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
          <input
            id="crownpass-credential"
            value={credential}
            onChange={(event) => setCredential(event.target.value)}
            autoComplete="off"
            style={{ flex: 1, padding: 10 }}
          />
          <button type="submit" disabled={busy || !credential.trim()}>
            {busy ? "Checking…" : "Check In"}
          </button>
        </div>
      </form>
    </main>
  );
}

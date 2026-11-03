import { useEffect, useRef, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { crownApiClient } from "../api/client.js";
import { getAccessToken, getSelectedSchoolId } from "../utils/authClient.js";

const BASE = "/api/v1/aftercare/daycare";
const METHODS = [
  ["GOVERNMENT_PHOTO_ID", "Government photo ID inspected in person"],
  ["APPROVED_PHOTO_ROSTER", "Approved photo roster"],
  ["PERSONALLY_KNOWN", "Personally known to releasing staff"],
];
const sameContext = (context) => Boolean(context?.school && context.token) &&
  context.school === getSelectedSchoolId() && context.token === getAccessToken();

export default function DiademReleaseReview({ siteId, attendance, onCancel, onReleased }) {
  const [options, setOptions] = useState(null);
  const [status, setStatus] = useState("");
  const [scope, setScope] = useState(null);
  const [selected, setSelected] = useState("");
  const [method, setMethod] = useState("");
  const [attested, setAttested] = useState(false);
  const [error, setError] = useState("");
  const [locked, setLocked] = useState(false);
  const [busy, setBusy] = useState(false);
  const attempted = useRef(false);

  useEffect(() => {
    const context = { school: getSelectedSchoolId(), token: getAccessToken() };
    let active = true;
    attempted.current = false;
    setOptions(null); setStatus(""); setScope(null); setSelected("");
    setMethod(""); setAttested(false); setError(""); setLocked(false);
    if (!sameContext(context)) {
      setError("Authenticated school and staff session required.");
      return () => { active = false; };
    }
    crownApiClient.get(
      `${BASE}/sites/${siteId}/attendance/${attendance.attendance_id}/release-authorities/`
    ).then(({ data }) => {
      if (!active || !sameContext(context)) return;
      if (data?.site_id !== siteId || data.attendance_id !== attendance.attendance_id ||
          !["candidates_only", "overnight_director_review_required"].includes(data.status) ||
          !Array.isArray(data.options) || !data.options.every(
            (item) => typeof item.authority_id === "string" && typeof item.guardian_name === "string"
          )) throw new Error("Pickup evidence failed custody scope verification.");
      setScope(context); setOptions(data.options); setStatus(data.status);
    }).catch((err) => {
      if (active && sameContext(context)) {
        setError(err.message || "Pickup evidence unavailable."); setLocked(true);
      }
    });
    return () => { active = false; };
  }, [siteId, attendance.attendance_id]);

  async function submit(event) {
    event.preventDefault();
    if (!sameContext(scope)) {
      setLocked(true);
      setError("Staff session or school context changed. Close this review, refresh the custody roster, and reverify the recipient. No release request was sent.");
      return;
    }
    if (attempted.current || busy || locked || !attested ||
        status !== "candidates_only" || !attendance.room_id ||
        !options?.some((item) => item.authority_id === selected) ||
        !METHODS.some(([code]) => code === method)) return;
    attempted.current = true;
    setBusy(true); setError("");
    try {
      const { data } = await crownApiClient.post(`${BASE}/attendance/release/`, {
        site_id: siteId, room_id: attendance.room_id,
        attendance_id: attendance.attendance_id, guardian_authority_id: selected,
        identity_method: method, identity_verified: true, request_key: crypto.randomUUID(),
      });
      if (!sameContext(scope)) return;
      if (data?.status !== "released" || data.attendance_id !== attendance.attendance_id)
        throw new Error("Server custody confirmation did not match the selected attendance.");
      onReleased();
    } catch (err) {
      if (sameContext(scope)) {
        setLocked(true);
        setError(`Release not confirmed: ${err.message || "request failed"}. Refresh and reverify current custody; do not retry automatically.`);
      }
    } finally {
      if (sameContext(scope)) setBusy(false);
    }
  }

  return <section aria-label={`Pickup review for ${attendance.child_name}`}>
    <h3>Verified pickup review — {attendance.child_name}</h3>
    <p>Verify the person's identity in person. The server independently rechecks current authority, staff coverage, and custody at confirmation.</p>
    {error && <p role="alert">{error}</p>}
    {!options && !error && <p role="status">Checking current pickup authority…</p>}
    {status === "overnight_director_review_required" &&
      <p role="alert">Care date changed: normal release is blocked; escalate for director review.</p>}
    {status === "candidates_only" && options?.length === 0 &&
      <p role="alert">No verified recipient available. Do not release the child.</p>}
    {status === "candidates_only" && options?.length > 0 &&
      <form onSubmit={submit}>
        <label>Verified pickup recipient
          <select required value={selected} disabled={busy || locked}
            onChange={(event) => { setSelected(event.target.value); setAttested(false); }}>
            <option value="">Select recipient</option>
            {options.map((item) => <option key={item.authority_id} value={item.authority_id}>
              {item.guardian_name}
            </option>)}
          </select>
        </label>
        <label>Identity verification method
          <select required value={method} disabled={busy || locked}
            onChange={(event) => { setMethod(event.target.value); setAttested(false); }}>
            <option value="">Choose method actually performed</option>
            {METHODS.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
          </select>
        </label>
        <label>
          <input type="checkbox" required checked={attested} disabled={busy || locked}
            onChange={(event) => setAttested(event.target.checked)} />
          I verified this person's identity and approve the in-person handoff.
        </label>
        <button type="submit" disabled={busy || locked || !selected || !method || !attested}>
          {busy ? "Recording custody handoff…" : "Confirm verified handoff"}
        </button>
      </form>}
    <button type="button" onClick={onCancel} disabled={busy}>Cancel review</button>
  </section>;
}

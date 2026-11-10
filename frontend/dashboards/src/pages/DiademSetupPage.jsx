import { useCallback, useEffect, useRef, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { crownApiClient } from "../api/client.js";
import { getAccessToken, getSelectedSchoolId, SCHOOL_CONTEXT_CHANGE_EVENT } from "../utils/authClient.js";

const BASE = "/api/v1/aftercare/daycare/setup/sites/";
const contextKey = () => `${getSelectedSchoolId()}:${getAccessToken()}`;
const emptySite = { code: "", name: "", operating_mode: "", jurisdiction: "US-DE" };
const emptyRoom = { code: "", name: "", licensed_capacity: "", max_children_per_staff: "",
  proposed_min_age_months: "", proposed_max_age_months: "", policy_source: "",
  proposed_policy_from: "", proposed_policy_until: "" };

export default function DiademSetupPage() {
  const [scope, setScope] = useState(contextKey);
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [roomReadback, setRoomReadback] = useState(null);
  const roomRequest = useRef(0);
  const [siteForm, setSiteForm] = useState(emptySite);
  const [roomForm, setRoomForm] = useState(emptyRoom);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [readback, setReadback] = useState(null);
  const school = getSelectedSchoolId();
  const current = useCallback(() => scope === contextKey() && Boolean(getSelectedSchoolId()), [scope]);

  useEffect(() => {
    const changed = () => setScope(contextKey());
    for (const event of [SCHOOL_CONTEXT_CHANGE_EVENT, "focus", "storage"]) window.addEventListener(event, changed);
    return () => {
      for (const event of [SCHOOL_CONTEXT_CHANGE_EVENT, "focus", "storage"]) window.removeEventListener(event, changed);
    };
  }, []);

  useEffect(() => {
    let live = true;
    setSites([]); setRoomReadback(null); setReadback(null); setError(""); setMessage(""); setBusy(false);
    setSiteId(""); setSiteForm(emptySite); setRoomForm(emptyRoom);
    if (!school || !current()) return () => { live = false; };
    setBusy(true);
    crownApiClient.get(BASE).then(({ data }) => {
      if (!live || !current()) return;
      if (data?.school_id !== school || !Array.isArray(data.sites)) throw new Error("Center scope could not be verified.");
      setSites(data.sites); setSiteId(data.sites[0]?.site_id || "");
      setReadback({ scope, asOf: data.as_of, source: data.source });
    }).catch((err) => { if (live && current()) setError(err.message || "Center setup unavailable."); })
      .finally(() => { if (live && current()) setBusy(false); });
    return () => { live = false; };
  }, [scope, revision, school, current]);

  useEffect(() => {
    let live = true;
    const version = ++roomRequest.current;
    setRoomReadback(null); setRoomForm(emptyRoom);
    if (!siteId || !current()) return () => { live = false; };
    crownApiClient.get(`${BASE}${siteId}/rooms/`).then(({ data }) => {
      if (!live || !current() || version !== roomRequest.current) return;
      if (data?.school_id !== school || data.site_id !== siteId || !Array.isArray(data.rooms))
        throw new Error("Room scope could not be verified.");
      setRoomReadback({ scope, siteId, data });
    }).catch((err) => { if (live && current() && version === roomRequest.current) setError(err.message || "Rooms unavailable."); });
    return () => { live = false; };
  }, [siteId, scope, revision, school, current]);

  async function submit(event, room = false) {
    event.preventDefault();
    if (!current() || busy || (room && !siteId)) return;
    const submittedSite = siteId;
    const version = room ? ++roomRequest.current : roomRequest.current;
    setBusy(true); setError(""); setMessage("");
    const values = room ? Object.fromEntries(Object.entries(roomForm).map(([key, value]) => [key,
      ["code", "name", "policy_source"].includes(key) ? value : value === "" ? null
        : key.startsWith("proposed_policy_") ? value : Number(value)])) : siteForm;
    try {
      await crownApiClient.post(room ? `${BASE}${siteId}/rooms/` : BASE, values);
      if (!current()) return;
      if (room) {
        const { data } = await crownApiClient.get(`${BASE}${submittedSite}/rooms/`);
        if (!current() || version !== roomRequest.current) return;
        if (data?.school_id !== school || data.site_id !== submittedSite || !Array.isArray(data.rooms))
          throw new Error("Saved room readback could not be verified.");
        setRoomReadback({ scope, siteId: submittedSite, data }); setRoomForm(emptyRoom);
      } else {
        const { data } = await crownApiClient.get(BASE);
        if (!current()) return;
        if (data?.school_id !== school || !Array.isArray(data.sites)) throw new Error("Saved center readback could not be verified.");
        setSites(data.sites);
        setSiteId(data.sites.find((site) => site.code === values.code)?.site_id || "");
        setSiteForm(emptySite); setReadback({ scope, asOf: data.as_of, source: data.source });
      }
      setMessage("Inactive configuration saved and read back. Policy approval is still required.");
    } catch (err) {
      if (current()) setError(err.message || "Configuration was not saved.");
    } finally { if (current()) setBusy(false); }
  }

  const visible = current() && readback?.scope === scope;
  const currentRoomReadback = visible && roomReadback?.scope === scope && roomReadback.siteId === siteId ? roomReadback.data : null;
  const rooms = currentRoomReadback?.rooms || [];
  const field = (form, setter, key, label, type = "text", required = false) => <label key={key} style={{ display: "block", marginBottom: 8 }}>
    {label}<input name={key} type={type} required={required} value={form[key]}
      min={type === "number" ? (key.includes("age") ? 0 : 1) : undefined}
      onChange={(event) => setter((old) => ({ ...old, [key]: event.target.value }))} />
  </label>;
  return <CrownLayout title="Diadem center and room setup" subtitle="Director configuration review">
    <p>New centers and rooms stay inactive. Admission requires separately verified licensing policy, enrollment and staffing.</p>
    <p>Jurisdiction: Delaware. Proposed values and a director role do not establish licensing or staff qualification.</p>
    {busy && <p role="status">Loading or saving configuration…</p>}
    {error && <p role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    <button type="button" disabled={busy} onClick={() => setRevision((n) => n + 1)}>Refresh configuration</button>
    {visible && <>
      <p>Observed at {readback.asOf}. Source: {readback.source}.</p>
      <section aria-labelledby="center-setup-title">
        <h2 id="center-setup-title">Create inactive center</h2>
        <form onSubmit={(event) => submit(event)}>
          <fieldset disabled={busy}><legend>Center details</legend>
            {field(siteForm, setSiteForm, "name", "Center name", "text", true)}
            {field(siteForm, setSiteForm, "code", "Center code", "text", true)}
            <label>Operating mode<select required value={siteForm.operating_mode} onChange={(event) => setSiteForm({ ...siteForm, operating_mode: event.target.value })}>
              <option value="">Choose operating mode</option><option value="STANDALONE">Standalone childcare</option><option value="INTEGRATED">CROWN integrated</option>
            </select></label>
            <button type="submit">Save inactive center</button>
          </fieldset>
        </form>
        {!sites.length && <p>No centers configured.</p>}
        <ul>{sites.map((site) => <li key={site.site_id}>{site.name} — {site.is_active ? "active record" : "inactive"}; {site.operating_mode || "mode not recorded"}; {site.jurisdiction || "jurisdiction not recorded"}</li>)}</ul>
      </section>
      <section aria-labelledby="room-setup-title">
        <h2 id="room-setup-title">Create inactive room</h2>
        <label>Room center<select value={siteId} disabled={busy || !sites.length} onChange={(event) => { setRoomReadback(null); setError(""); setSiteId(event.target.value); }}>
          {!siteId && <option value="">No center selected</option>}
          {sites.map((site) => <option key={site.site_id} value={site.site_id}>{site.name}</option>)}
        </select></label>
        <form onSubmit={(event) => submit(event, true)}>
          <fieldset disabled={busy || !siteId}><legend>Proposed room policy — unverified</legend>
            {field(roomForm, setRoomForm, "name", "Room name", "text", true)}
            {field(roomForm, setRoomForm, "code", "Room code", "text", true)}
            {field(roomForm, setRoomForm, "licensed_capacity", "Proposed licensed capacity", "number")}
            {field(roomForm, setRoomForm, "max_children_per_staff", "Proposed maximum children per staff member", "number")}
            {field(roomForm, setRoomForm, "proposed_min_age_months", "Proposed minimum age in months", "number")}
            {field(roomForm, setRoomForm, "proposed_max_age_months", "Proposed maximum age in months", "number")}
            {field(roomForm, setRoomForm, "proposed_policy_from", "Proposed policy start", "date")}
            {field(roomForm, setRoomForm, "proposed_policy_until", "Proposed policy end", "date")}
            {field(roomForm, setRoomForm, "policy_source", "Policy source for qualified review")}
            <button type="submit">Save inactive room</button>
          </fieldset>
        </form>
        {currentRoomReadback && <p>Rooms observed at {currentRoomReadback.as_of}. Source: {currentRoomReadback.source}.</p>}
        {siteId && !currentRoomReadback && !error && <p role="status">Loading room records…</p>}
        {currentRoomReadback && !rooms.length && <p>No room records returned.</p>}
        <ul>{rooms.map((room) => <li key={room.room_id}>{room.name} — {room.is_active ? "active record" : "inactive"}; capacity {room.licensed_capacity ?? "not recorded"}; maximum children per staff {room.max_children_per_staff ?? "not recorded"}; proposed age {room.proposed_min_age_months ?? "unknown"}–{room.proposed_max_age_months ?? "unknown"} months; proposed dates {room.proposed_policy_from || "unknown"} to {room.proposed_policy_until || "not recorded"}; policy review {room.policy_verified_at || "not recorded"}</li>)}</ul>
      </section>
    </>}
  </CrownLayout>;
}

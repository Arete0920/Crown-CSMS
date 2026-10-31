import { useEffect, useState } from "react";
import { authenticatedFetch, getAccessToken } from "../utils/authClient.js";

async function loadGrantor(url) {
  const response = await authenticatedFetch(url, {
    method: "GET", omitSchoolContext: true, cache: "no-store",
  });
  const data = await response.json();
  if (!data || typeof data !== "object") throw new Error("Invalid grantor response.");
  return data;
}

const money = (cents) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD",
}).format(Number(cents || 0) / 100);

export default function JirehSGODashboard() {
  const token = getAccessToken();
  const [organizations, setOrganizations] = useState(null);
  const [organizationId, setOrganizationId] = useState("");
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // A previous member's grantor records must not remain visible when a
    // session ends or the authenticated principal changes.
    setOrganizations(null);
    setOrganizationId("");
    setOverview(null);
    setError("");
    setLoading(false);
    if (!token) return;
    let live = true;
    setLoading(true);
    loadGrantor("/api/v1/jireh-sgo/organizations/").then((data) => {
      if (!live) return;
      if (!Array.isArray(data.organizations) || data.funds_status !== "NONCASH_ONLY")
        throw new Error("Unexpected grantor scope.");
      setOrganizations(data.organizations);
      setOrganizationId(data.organizations[0]?.id || "");
      setError("");
    }).catch(() => {
      if (live) { setOverview(null); setOrganizations([]); setError("SGO membership could not be verified."); }
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [token]);

  useEffect(() => {
    if (!token || !organizationId) { setOverview(null); return; }
    let live = true;
    setOverview(null);
    setLoading(true);
    loadGrantor("/api/v1/jireh-sgo/organizations/" + encodeURIComponent(organizationId) + "/overview/")
      .then((data) => {
        if (!live) return;
        if (data.organization?.id !== organizationId ||
            data.funds_status !== "NONCASH_ONLY" || !Array.isArray(data.programs))
          throw new Error("Grantor context mismatch.");
        setOverview(data);
        setError("");
      }).catch(() => {
        if (live) { setOverview(null); setError("Grantor data unavailable. No figures displayed."); }
      }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [token, organizationId]);

  return <main style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem" }}>
    <h1>Jireh SGO — Grantor Overview</h1>
    <p>Standalone, noncash pilot workspace. No settlement or payments enabled.</p>
    <p role="note">Commitments are not funded, cleared, allocated, or paid.</p>
    {!token && <p role="alert">Authorized SGO sign-in is required.</p>}
    {token && loading && <p role="status">Verifying grantor membership and records…</p>}
    {token && error && <p role="alert">{error}</p>}
    {token && organizations?.length === 0 && !error && <p>No active SGO membership is assigned.</p>}
    {token && organizations?.length > 0 && <section aria-label="SGO membership">
      <label htmlFor="sgo-organization">Grantor organization</label>
      <select id="sgo-organization" value={organizationId}
        onChange={(event) => setOrganizationId(event.target.value)}>
        {organizations.map((organization) => <option key={organization.id} value={organization.id}>
          {organization.name} ({organization.role})
        </option>)}
      </select>
    </section>}
    {token && overview && !loading && <>
      <section aria-label="Noncash aggregate totals">
        <h2>{overview.organization.name}</h2>
        <p>Authorized role: {overview.role}</p>
        <p>Programs: {overview.totals.programs}; applications: {overview.totals.applications}</p>
        <p>Noncash commitments: {money(overview.totals.noncash_committed_cents)}</p>
      </section>
      <section aria-label="SGO programs">
        <h2>Versioned programs</h2>
        {overview.programs.length === 0 ? <p>No versioned programs yet.</p> : <table>
          <thead><tr><th scope="col">Program</th><th scope="col">Year</th>
          <th scope="col">Source</th><th scope="col">Policy</th>
          <th scope="col">Applications</th><th scope="col">Eligible</th>
          <th scope="col">Unreviewed</th><th scope="col">Noncash committed</th></tr></thead>
          <tbody>{overview.programs.map((row) => <tr key={row.id}>
            <th scope="row">{row.name}</th><td>{row.year}</td><td>{row.source}</td>
            <td>{row.policy_version}</td><td>{row.applications}</td>
            <td>{row.eligible}</td><td>{row.unreviewed}</td>
            <td>{money(row.noncash_committed_cents)}</td>
          </tr>)}</tbody>
        </table>}
      </section>
    </>}
  </main>;
}

/**
 * GivePage  donation upsell (Gift checkout) + recurring Pledge creation.
 * Calls POST /api/v1/advancement/gift/checkout/   pending Gift
 *       POST /api/v1/advancement/pledges/create/  Pledge
 *       GET  /api/v1/advancement/campaigns/       active campaigns for selection
 */
import { useState, useEffect } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}
function authHeaders() {
  const { token, schoolId } = getSession();
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

const AMOUNTS = [25, 50, 100, 250, 500];
const FREQUENCIES = [
  { value: "one_time", label: "One-time" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "annual", label: "Annual" },
];

export default function GivePage() {
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);

  // Gift form state
  const [giftForm, setGiftForm] = useState({
    amount: "",
    campaign_id: "",
    restricted: false,
    restriction_label: "",
    memo: "",
  });
  const [giftSubmitting, setGiftSubmitting] = useState(false);
  const [giftResult, setGiftResult] = useState(null);
  const [giftError, setGiftError] = useState(null);

  // Pledge form state
  const [pledgeForm, setPledgeForm] = useState({
    total_amount: "",
    frequency: "monthly",
    campaign_id: "",
    start_date: new Date().toISOString().slice(0, 10),
  });
  const [pledgeSubmitting, setPledgeSubmitting] = useState(false);
  const [pledgeResult, setPledgeResult] = useState(null);
  const [pledgeError, setPledgeError] = useState(null);

  useEffect(() => {
    globalThis.fetch(`${apiBase()}/api/v1/advancement/campaigns/?status=active`, {
      headers: authHeaders(),
    })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then((d) => setCampaigns(d.results ?? d))
      .catch(() => setCampaigns([]))
      .finally(() => setLoadingCampaigns(false));
  }, []);

  async function handleGiftSubmit(e) {
    e.preventDefault();
    setGiftSubmitting(true);
    setGiftError(null);
    setGiftResult(null);
    try {
      const payload = {
        amount: parseFloat(giftForm.amount),
        restricted: giftForm.restricted,
        restriction_label: giftForm.restriction_label,
        memo: giftForm.memo,
      };
      if (giftForm.campaign_id) payload.campaign_id = giftForm.campaign_id;

      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/gift/checkout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setGiftError(data?.detail || `HTTP ${res.status}`);
        return;
      }
      setGiftResult(data);
      setGiftForm({ amount: "", campaign_id: "", restricted: false, restriction_label: "", memo: "" });
    } catch (err) {
      setGiftError(String(err));
    } finally {
      setGiftSubmitting(false);
    }
  }

  async function handlePledgeSubmit(e) {
    e.preventDefault();
    setPledgeSubmitting(true);
    setPledgeError(null);
    setPledgeResult(null);
    try {
      const payload = {
        total_amount: parseFloat(pledgeForm.total_amount),
        frequency: pledgeForm.frequency,
        start_date: pledgeForm.start_date,
      };
      if (pledgeForm.campaign_id) payload.campaign_id = pledgeForm.campaign_id;

      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/pledges/create/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setPledgeError(data?.detail || `HTTP ${res.status}`);
        return;
      }
      setPledgeResult(data);
      setPledgeForm({ total_amount: "", frequency: "monthly", campaign_id: "", start_date: new Date().toISOString().slice(0, 10) });
    } catch (err) {
      setPledgeError(String(err));
    } finally {
      setPledgeSubmitting(false);
    }
  }

  const inputStyle = {
    width: "100%",
    padding: "0.6rem 0.9rem",
    border: "1px solid var(--crown-compat-color-9643a6d44f)",
    borderRadius: 6,
    fontSize: "0.95rem",
    boxSizing: "border-box",
  };
  const labelStyle = { display: "block", fontWeight: 600, marginBottom: 4, fontSize: "0.9rem", color: "var(--crown-compat-color-a95c525e33)" };
  const fieldStyle = { marginBottom: "1rem" };
  const cardStyle = {
    background: "var(--crown-compat-color-e08de71387)",
    border: "1px solid var(--crown-compat-color-bfd4f8ffca)",
    borderRadius: 10,
    padding: "1.5rem",
    marginBottom: "2rem",
    boxShadow: "0 1px 3px var(--crown-compat-color-957060f46c)",
  };

  return (
    <div style={{ maxWidth: 620, margin: "0 auto", padding: "2rem 1rem", fontFamily: "var(--crown-font-family)" }}>
      <h1 style={{ fontSize: "1.6rem", fontWeight: 700, marginBottom: "2rem" }}>Give</h1>

      {/* ---- One-time gift ---- */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, marginBottom: "1.25rem" }}>One-time Gift</h2>

        {giftResult && (
          <div style={{ background: "var(--crown-compat-color-64033be9a6)", border: "1px solid var(--crown-compat-color-7d4ff8ff7b)", borderRadius: 6, padding: "0.75rem 1rem", marginBottom: "1rem", color: "var(--crown-compat-color-7d4ff8ff7b)", fontWeight: 600 }}>
            Gift created! ID: {giftResult.id}  Status: {giftResult.status}
          </div>
        )}
        {giftError && (
          <div style={{ background: "var(--crown-compat-color-4b54505300)", border: "1px solid var(--crown-compat-color-59dbd12595)", borderRadius: 6, padding: "0.75rem 1rem", marginBottom: "1rem", color: "var(--crown-compat-color-59dbd12595)" }}>
            {giftError}
          </div>
        )}

        <form onSubmit={handleGiftSubmit}>
          <div style={fieldStyle}>
            <label htmlFor="gift-amount" style={labelStyle}>Amount ($)</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
              {AMOUNTS.map((a) => (
                <button
                  key={a}
                  type="button"
                  onClick={() => setGiftForm((f) => ({ ...f, amount: String(a) }))}
                  style={{
                    padding: "0.4rem 0.9rem",
                    border: "1px solid",
                    borderColor: giftForm.amount === String(a) ? "var(--crown-compat-color-1d4a6b66ff)" : "var(--crown-compat-color-9643a6d44f)",
                    background: giftForm.amount === String(a) ? "var(--crown-compat-color-61eaaf6f10)" : "var(--crown-compat-color-e08de71387)",
                    color: giftForm.amount === String(a) ? "var(--crown-compat-color-1d4a6b66ff)" : "var(--crown-compat-color-a95c525e33)",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  ${a}
                </button>
              ))}
            </div>
            <input
              type="number"
              min="1"
              step="0.01"
              placeholder="Other amount"
              value={giftForm.amount}
              onChange={(e) => setGiftForm((f) => ({ ...f, amount: e.target.value }))}
              style={inputStyle}
              required
            />
          </div>

          <div style={fieldStyle}>
            <label htmlFor="gift-campaign" style={labelStyle}>Campaign (optional)</label>
            <select
              value={giftForm.campaign_id}
              onChange={(e) => setGiftForm((f) => ({ ...f, campaign_id: e.target.value }))}
              style={inputStyle}
              disabled={loadingCampaigns}
            >
              <option value=""> No specific campaign </option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div style={{ ...fieldStyle, display: "flex", alignItems: "center", gap: 8 }}>
            <input
              id="restricted"
              type="checkbox"
              checked={giftForm.restricted}
              onChange={(e) => setGiftForm((f) => ({ ...f, restricted: e.target.checked }))}
            />
            <label htmlFor="restricted" style={{ fontWeight: 400, fontSize: "0.9rem", color: "var(--crown-compat-color-a95c525e33)" }}>
              Restrict this gift to a specific purpose
            </label>
          </div>

          {giftForm.restricted && (
            <div style={fieldStyle}>
              <label htmlFor="gift-restriction-label" style={labelStyle}>Restriction label</label>
              <input
                type="text"
                placeholder="e.g. Library Fund"
                value={giftForm.restriction_label}
                onChange={(e) => setGiftForm((f) => ({ ...f, restriction_label: e.target.value }))}
                style={inputStyle}
                maxLength={255}
              />
            </div>
          )}

          <div style={fieldStyle}>
            <label htmlFor="gift-memo" style={labelStyle}>Memo (optional)</label>
            <input
              type="text"
              placeholder="In honor of"
              value={giftForm.memo}
              onChange={(e) => setGiftForm((f) => ({ ...f, memo: e.target.value }))}
              style={inputStyle}
              maxLength={255}
            />
          </div>

          <button
            type="submit"
            disabled={giftSubmitting || !giftForm.amount}
            style={{
              width: "100%",
              padding: "0.75rem",
              background: "var(--crown-compat-color-1d4a6b66ff)",
              color: "var(--crown-compat-color-e08de71387)",
              border: "none",
              borderRadius: 6,
              fontWeight: 700,
              fontSize: "1rem",
              cursor: giftSubmitting ? "wait" : "pointer",
            }}
          >
            {giftSubmitting ? "Processing" : "Give Now"}
          </button>
        </form>
      </div>

      {/* ---- Recurring pledge ---- */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, marginBottom: "1.25rem" }}>Recurring Pledge</h2>

        {pledgeResult && (
          <div style={{ background: "var(--crown-compat-color-64033be9a6)", border: "1px solid var(--crown-compat-color-7d4ff8ff7b)", borderRadius: 6, padding: "0.75rem 1rem", marginBottom: "1rem", color: "var(--crown-compat-color-7d4ff8ff7b)", fontWeight: 600 }}>
            Pledge created! ${pledgeResult.total_amount} {pledgeResult.frequency}  Status: {pledgeResult.status}
          </div>
        )}
        {pledgeError && (
          <div style={{ background: "var(--crown-compat-color-4b54505300)", border: "1px solid var(--crown-compat-color-59dbd12595)", borderRadius: 6, padding: "0.75rem 1rem", marginBottom: "1rem", color: "var(--crown-compat-color-59dbd12595)" }}>
            {pledgeError}
          </div>
        )}

        <form onSubmit={handlePledgeSubmit}>
          <div style={fieldStyle}>
            <label htmlFor="pledge-total-amount" style={labelStyle}>Total pledge amount ($)</label>
            <input
              type="number"
              min="1"
              step="0.01"
              placeholder="e.g. 1200"
              value={pledgeForm.total_amount}
              onChange={(e) => setPledgeForm((f) => ({ ...f, total_amount: e.target.value }))}
              style={inputStyle}
              required
            />
          </div>

          <div style={fieldStyle}>
            <div style={labelStyle}>Frequency</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {FREQUENCIES.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setPledgeForm((f) => ({ ...f, frequency: value }))}
                  style={{
                    padding: "0.4rem 0.9rem",
                    border: "1px solid",
                    borderColor: pledgeForm.frequency === value ? "var(--crown-compat-color-1d4a6b66ff)" : "var(--crown-compat-color-9643a6d44f)",
                    background: pledgeForm.frequency === value ? "var(--crown-compat-color-61eaaf6f10)" : "var(--crown-compat-color-e08de71387)",
                    color: pledgeForm.frequency === value ? "var(--crown-compat-color-1d4a6b66ff)" : "var(--crown-compat-color-a95c525e33)",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div style={fieldStyle}>
            <label htmlFor="pledge-start-date" style={labelStyle}>Start date</label>
            <input
              type="date"
              value={pledgeForm.start_date}
              onChange={(e) => setPledgeForm((f) => ({ ...f, start_date: e.target.value }))}
              style={inputStyle}
              required
            />
          </div>

          <div style={fieldStyle}>
            <label htmlFor="gift-campaign" style={labelStyle}>Campaign (optional)</label>
            <select
              value={pledgeForm.campaign_id}
              onChange={(e) => setPledgeForm((f) => ({ ...f, campaign_id: e.target.value }))}
              style={inputStyle}
              disabled={loadingCampaigns}
            >
              <option value=""> No specific campaign </option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={pledgeSubmitting || !pledgeForm.total_amount}
            style={{
              width: "100%",
              padding: "0.75rem",
              background: "var(--crown-compat-color-7d4ff8ff7b)",
              color: "var(--crown-compat-color-e08de71387)",
              border: "none",
              borderRadius: 6,
              fontWeight: 700,
              fontSize: "1rem",
              cursor: pledgeSubmitting ? "wait" : "pointer",
            }}
          >
            {pledgeSubmitting ? "Creating pledge" : "Create Pledge"}
          </button>
        </form>
      </div>
    </div>
  );
}

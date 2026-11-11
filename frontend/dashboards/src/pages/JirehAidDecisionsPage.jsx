import { useCallback, useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiJson } from "../lib/api.js";
import {
  getAccessToken, getSelectedSchoolId, SCHOOL_CONTEXT_CHANGE_EVENT,
} from "../utils/authClient.js";
import {
  requireAidOverview, requireCurrentAidYear, dollarsToCents,
  verifiedAcceptedAward, acceptedFaceValue,
} from "./jirehAidChecks.js";

const BOX = { background: "var(--crown-surface, #fff)", border: "1px solid #d8e3f3", borderRadius: 12, padding: 20, marginBottom: 18 };
const ROW = { display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 12 };
const FINANCE_BUCKETS = ["NEED", "MISSION", "MERIT", "HARDSHIP", "MARKETING"];
const identity = () => String(getSelectedSchoolId()) + ":" + String(getAccessToken());
const cash = (value) => "$" + (Number(value || 0) / 100).toFixed(2);
const messageFor = (error) => error?.response?.data?.detail || error?.response?.data?.error || error?.message || "Request failed.";

export default function JirehAidDecisionsPage() {
  const [scope, setScope] = useState(identity);
  const [yearId, setYearId] = useState("");
  const [yearName, setYearName] = useState("");
  const [overview, setOverview] = useState(null);
  const [dashboardMeta, setDashboardMeta] = useState(null);
  const [applicationId, setApplicationId] = useState("");
  const [review, setReview] = useState(null);
  const [studentId, setStudentId] = useState("");
  const [bucket, setBucket] = useState("NEED");
  const [tuition, setTuition] = useState("");
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [approvalText, setApprovalText] = useState("");
  const [approvalReason, setApprovalReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [unresolvedWrite, setUnresolvedWrite] = useState(false);
  const [revision, setRevision] = useState(0);
  const current = useCallback(() =>
    Boolean(getSelectedSchoolId()) && Boolean(getAccessToken()) && scope === identity(), [scope]);

  useEffect(() => {
    const changed = () => setScope(identity());
    for (const name of [SCHOOL_CONTEXT_CHANGE_EVENT, "crown:auth-context-changed", "storage", "focus", "pageshow"])
      window.addEventListener(name, changed);
    return () => {
      for (const name of [SCHOOL_CONTEXT_CHANGE_EVENT, "crown:auth-context-changed", "storage", "focus", "pageshow"])
        window.removeEventListener(name, changed);
    };
  }, []);

  useEffect(() => {
    let active = true;
    setYearId(""); setYearName(""); setOverview(null); setDashboardMeta(null);
    setApplicationId(""); setReview(null); setError(""); setNotice(""); setUnresolvedWrite(false);
    if (!current()) {
      setError("A verified school session is required.");
      return () => { active = false; };
    }
    apiJson("/api/v1/academics/years/?limit=100")
      .then((data) => {
        if (!active || !current()) return;
        const year = requireCurrentAidYear(data, getSelectedSchoolId());
        setYearId(String(year.year_id));
        setYearName(year.name);
      })
      .catch((failure) => { if (active && current()) setError(messageFor(failure)); });
    return () => { active = false; };
  }, [scope, current]);

  const readOverview = useCallback(async () => {
    if (!yearId || !current()) throw new Error("School and academic year must be verified.");
    const [raw, dashboard] = await Promise.all([
      apiJson("/api/aid/admin/overview/?academic_year_id=" + encodeURIComponent(yearId)),
      apiJson("/api/v1/dashboards/financial-aid/summary").catch(() => null),
    ]);
    const data = requireAidOverview(raw);
    const rows = [...data.applications, ...data.awards, ...data.budgets];
    if (rows.some((row) =>
      String(row.academic_year_id) !== String(yearId)
      || (row.school_id && String(row.school_id) !== String(getSelectedSchoolId())))) {
      throw new Error("Financial Aid overview contains inconsistent school/year records.");
    }
    const meta = dashboard?.meta;
    const live = meta?.served_from === "live_db"
      && String(meta.school_id) === String(getSelectedSchoolId())
      && String(meta.academic_year_id) === String(yearId);
    if (current()) {
      setOverview(data);
      setDashboardMeta(live ? meta : null);
    }
    return { data, meta: live ? meta : null };
  }, [current, yearId]);

  useEffect(() => {
    let active = true;
    setOverview(null); setDashboardMeta(null); setReview(null); setApplicationId("");
    if (yearId && current()) {
      readOverview().catch((failure) => {
        if (active && current()) setError(messageFor(failure));
      });
    }
    return () => { active = false; };
  }, [yearId, readOverview, revision, current]);

  useEffect(() => {
    let active = true;
    setReview(null); setStudentId(""); setReviewConfirmed(false);
    setApprovalText(""); setApprovalReason("");
    if (applicationId && current()) {
      apiJson("/api/aid/admin/applications/" + encodeURIComponent(applicationId) + "/review/")
        .then((data) => {
          if (!active || !current()) return;
          if (String(data?.application_id) !== String(applicationId)
            || !Array.isArray(data.students) || !Array.isArray(data.review_signals)) {
            throw new Error("Jireh review returned an invalid case or student contract.");
          }
          setReview(data);
          setStudentId(data.students.length === 1 ? String(data.students[0].id) : "");
        })
        .catch((failure) => { if (active && current()) setError(messageFor(failure)); });
    }
    return () => { active = false; };
  }, [applicationId, current, revision]);

  const selected = overview?.applications.find((item) => String(item.id) === String(applicationId));
  const awards = (overview?.awards || []).filter((award) => String(award.aid_application_id) === String(applicationId));
  const duplicateOffer = awards.some((award) =>
    String(award.student_id) === String(studentId) && award.award_type === bucket
    && award.decision_status !== "DECLINED");

  async function recommend(event) {
    event.preventDefault();
    if (busy || unresolvedWrite || !reviewConfirmed || !review || !selected || !current()) return;
    if (!review.students.some((student) => String(student.id) === String(studentId))) {
      setError("Choose a student from the reviewed family."); return;
    }
    if (duplicateOffer) { setError("An active offer already exists for this student and category."); return; }
    let gross;
    try { gross = dollarsToCents(tuition); }
    catch (failure) { setError(messageFor(failure)); return; }
    setBusy(true); setError(""); setNotice(""); setUnresolvedWrite(true);
    try {
      const created = await apiJson("/api/aid/admin/recommend-award/", {
        method: "POST",
        body: JSON.stringify({
          application_id: Number(applicationId), student_id: studentId,
          bucket, gross_tuition_cents: gross,
        }),
      });
      const checked = await readOverview();
      const award = checked.data.awards.find((item) =>
        String(item.id) === String(created?.award?.id)
        && String(item.aid_application_id) === String(applicationId)
        && String(item.student_id) === String(studentId)
        && item.decision_status === "OFFERED" && !item.ledger_entry_id);
      if (!award) throw new Error("Offer requires independent saved-record reconciliation.");
      if (!current()) return;
      setNotice("Offer #" + award.id + " saved and independently verified; no financial posting occurred.");
      setUnresolvedWrite(false);
    } catch (failure) {
      if (current()) setError("Recommendation outcome needs reconciliation before retry: " + messageFor(failure));
    } finally { if (current()) setBusy(false); }
  }

  async function approve(award) {
    if (busy || unresolvedWrite || !reviewConfirmed || !current() || approvalText !== "APPROVE"
      || award.decision_status !== "OFFERED" || Number(award.awarded_cents) <= 0) return;
    setBusy(true); setError(""); setNotice(""); setUnresolvedWrite(true);
    try {
      await apiJson("/api/aid/admin/awards/" + encodeURIComponent(award.id) + "/approve/", {
        method: "POST", body: JSON.stringify({ reason: approvalReason.trim() }),
      });
      const checked = await readOverview();
      const linked = verifiedAcceptedAward(checked.data, award.id, applicationId, award.student_id);
      if (!linked) throw new Error("The accepted award and linked AID ledger credit did not reconcile.");
      if (!checked.meta || checked.meta.accepted_award_face_value_cents !== acceptedFaceValue(checked.data)) {
        throw new Error("The authoritative live dashboard does not reconcile to accepted award records.");
      }
      if (!current()) return;
      setNotice("Accepted award #" + linked.id + " and noncash ledger credit verified; dashboard face value reconciled. No payment was made.");
      setUnresolvedWrite(false);
      setApprovalText(""); setApprovalReason("");
    } catch (failure) {
      if (current()) setError("Approval may have posted. Do not retry until records are reconciled: " + messageFor(failure));
    } finally { if (current()) setBusy(false); }
  }

  return <CrownLayout title="Jireh Financial Aid — Applications and Awards"
    subtitle="School-scoped operational case review; accepted award face value is not cash disbursement."
    right={<a href="/financial-aid-dashboard">View live aid dashboard</a>}>
    {error && <p role="alert" style={{ color: "#aa1722", fontWeight: 700 }}>{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {busy && <p role="status">Verifying the current operation…</p>}
    <section style={BOX}>
      <div style={ROW}>
        <h2 style={{ margin: 0 }}>Current aid year: {yearName || "Not verified"}</h2>
        <button type="button" disabled={busy || !yearId} onClick={() => {
          setError(""); setNotice(""); setUnresolvedWrite(false); setRevision((value) => value + 1);
        }}>Refresh and reconcile records</button>
      </div>
      <p>Dashboard truth: <strong>{dashboardMeta ? "Live canonical records" : "Not verified — fallback is not financial proof"}</strong>.</p>
      {dashboardMeta && <p>Current-year accepted awards: {dashboardMeta.accepted_award_records};
        accepted face value {cash(dashboardMeta.accepted_award_face_value_cents)};
        unposted accepted awards {dashboardMeta.accepted_without_ledger_count}.</p>}
      <p>Any unexpected response or authorization failure stops this workflow; no assumed or sample awards are displayed.</p>
    </section>
    <section style={BOX}>
      <h2>1. Review submitted family applications</h2>
      {!overview && <p>Loading authorized school applications…</p>}
      {overview && !overview.applications.length && <p>No canonical applications for the selected year.</p>}
      <div style={{ display: "grid", gap: 8 }}>
        {(overview?.applications || []).map((app) =>
          <button key={app.id} type="button" aria-pressed={String(app.id) === String(applicationId)}
            onClick={() => { setError(""); setNotice(""); setApplicationId(String(app.id)); }}
            style={{ padding: 12, textAlign: "left", borderRadius: 8,
              border: String(app.id) === String(applicationId) ? "2px solid #17439c" : "1px solid #ccc" }}>
            Application #{app.id} — {app.status} — submitted {app.submitted_at || "not yet"} — household size {app.household_size}
          </button>)}
      </div>
    </section>
    {selected && <section style={BOX}>
      <h2>2. Evidence and recommendation: application #{selected.id}</h2>
      {!review && <p>Loading the scoped financial case review…</p>}
      {review && <>
        <p>Financial profile: <strong>{review.financial_profile?.verification_status || "Missing"}</strong>.
          Review signals are advisory and do not constitute a committee decision.</p>
        <ul>{review.review_signals.map((signal) =>
          <li key={signal.code}><strong>{signal.severity}</strong>: {signal.summary}</li>)}</ul>
        {!review.review_signals.length && <p>No deterministic review flags returned.</p>}
        <label style={ROW}><input type="checkbox" checked={reviewConfirmed}
          onChange={(event) => setReviewConfirmed(event.target.checked)} />
          I reviewed this application's available evidence and acknowledge any missing items.</label>
        <form onSubmit={recommend}>
          <div style={ROW}>
            <label>Student in this family <select required value={studentId}
              onChange={(event) => setStudentId(event.target.value)}>
              <option value="">Choose student</option>
              {review.students.map((student) => <option key={student.id} value={student.id}>
                {student.first_name} {student.last_name} ({student.student_number})
              </option>)}
            </select></label>
            <label>Award category <select value={bucket} onChange={(event) => setBucket(event.target.value)}>
              {FINANCE_BUCKETS.map((kind) => <option key={kind} value={kind}>{kind}</option>)}
            </select></label>
            <label>Gross annual tuition, dollars <input required inputMode="decimal" value={tuition}
              placeholder="e.g. 12500.00" onChange={(event) => setTuition(event.target.value)} /></label>
          </div>
          <button type="submit" disabled={busy || unresolvedWrite || !reviewConfirmed || !studentId || duplicateOffer}>
            Calculate and save an OFFERED award
          </button>
          {duplicateOffer && <p>An active offer already exists for this category and student.</p>}
        </form>
      </>}
    </section>}
    {selected && <section style={BOX}>
      <h2>3. Authorized award decision and independent readback</h2>
      <p>Approval posts a tuition aid credit and updates the bucket budget. It does not move cash,
        record a committee vote, or automatically close a multistudent family application.</p>
      <p>Budget controls: {(overview?.budgets || []).map((budget) =>
        <span key={budget.id} style={{ marginRight: 15 }}>{budget.bucket}: {cash(budget.remaining_cents)} remaining</span>)}</p>
      {awards.map((award) => <div key={award.id} style={{ borderTop: "1px solid #ddd", padding: "12px 0" }}>
        <strong>#{award.id}</strong> — {award.award_type}, {cash(award.awarded_cents)} —
        <strong> {award.decision_status}</strong>; ledger {award.ledger_entry_id || "not posted"}
        {award.decision_status === "OFFERED" && Number(award.awarded_cents) > 0 && <>
          <div style={ROW}>
            <label>Approval reason <input value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} /></label>
            <label>Type APPROVE <input aria-label="Type APPROVE to authorize award"
              value={approvalText} onChange={(event) => setApprovalText(event.target.value)} /></label>
          </div>
          <button type="button" disabled={busy || unresolvedWrite || !reviewConfirmed || approvalText !== "APPROVE"}
            onClick={() => approve(award)}>Approve and verify ledger + dashboard</button>
        </>}
      </div>)}
      {!awards.length && <p>No award offers recorded for this application.</p>}
    </section>}
  </CrownLayout>;
}

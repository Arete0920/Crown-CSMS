import { useCallback, useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { authenticatedFetch, getAccessToken } from "../utils/authClient.js";

const base = "/api/v1/jireh-sgo";
const grades = ["K", ...Array.from({ length: 12 }, (_, i) => String(i + 1))];
const reasons = [
  ["GRADE_UNVERIFIED", "Confirm grade level"],
  ["PROGRAM_DETAIL_MISMATCH", "Verify program selection"],
  ["OTHER_NON_SENSITIVE", "Recheck application information"],
];
const card = {
  border: "1px solid var(--crown-border)", borderRadius: 8,
  background: "var(--crown-surface)", padding: "1rem", marginBottom: "1rem",
};

async function sgoRequest(path, { method = "GET", data } = {}) {
  const response = await authenticatedFetch(base + path, {
    method, omitSchoolContext: true, cache: "no-store",
    ...(data === undefined ? {} : {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  });
  return response.json();
}

export default function JirehSGOIntakePage() {
  const token = getAccessToken();
  const local = import.meta.env.VITE_LOCAL_DEMO === "1";
  const [loadedToken, setLoadedToken] = useState(null);
  const [families, setFamilies] = useState([]);
  const [processors, setProcessors] = useState([]);
  const [familyProgram, setFamilyProgram] = useState("");
  const [processorProgram, setProcessorProgram] = useState("");
  const [grade, setGrade] = useState("K");
  const [correctionGrade, setCorrectionGrade] = useState("K");
  const [consent, setConsent] = useState(false);
  const [application, setApplication] = useState(null);
  const [queue, setQueue] = useState([]);
  const [reason, setReason] = useState(reasons[0][0]);
  const [submissionKey, setSubmissionKey] = useState("");
  const [correctionKey, setCorrectionKey] = useState("");
  const [processorKey, setProcessorKey] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let live = true;
    setLoadedToken(null);
    setFamilies([]);
    setProcessors([]);
    setFamilyProgram("");
    setProcessorProgram("");
    setApplication(null);
    setQueue([]);
    setError("");
    setNotice("");
    setConsent(false);
    setSubmissionKey("");
    setCorrectionKey("");
    setProcessorKey("");
    if (!token || !local) return () => { live = false; };
    Promise.all([
      sgoRequest("/family/programs/"),
      sgoRequest("/processor/programs/"),
    ]).then(([family, processor]) => {
      if (!live) return;
      if (!family.synthetic_only || family.funds_status !== "NONCASH_ONLY"
          || !Array.isArray(family.programs)
          || processor.authority !== "PROCESSOR_VERIFICATION_ONLY"
          || !Array.isArray(processor.programs)) {
        throw new Error("Fictional authorization contract unavailable.");
      }
      setFamilies(family.programs);
      setProcessors(processor.programs);
      setFamilyProgram(family.programs[0]?.id || "");
      setProcessorProgram(processor.programs[0]?.id || "");
      setLoadedToken(token);
    }).catch(() => {
      if (live) setError("Fictional partner-program access could not be verified.");
    });
    return () => { live = false; };
  }, [token, local]);

  const family = families.find((item) => item.id === familyProgram);
  const processor = processors.find((item) => item.id === processorProgram);
  const authorized = !!token && local && loadedToken === token;

  useEffect(() => {
    let live = true;
    setApplication(null);
    setSubmissionKey("");
    setCorrectionKey("");
    if (!authorized || !family?.application_id) return () => { live = false; };
    sgoRequest("/family/applications/" + encodeURIComponent(family.application_id) + "/")
      .then((result) => {
        if (live && result.application?.program_id === family.id) {
          setApplication(result.application);
          setCorrectionGrade(result.application.grade_level);
        }
      }).catch(() => {
        if (live) setError("Submitted application could not be read back.");
      });
    return () => { live = false; };
  }, [authorized, family?.id, family?.application_id, token]);

  const refreshQueue = useCallback(async () => {
    if (!authorized || !processor) return;
    const result = await sgoRequest(
      "/processor/programs/" + encodeURIComponent(processor.id) + "/queue/",
    );
    if (result.authority !== "PROCESSOR_VERIFICATION_ONLY"
        || result.program_id !== processor.id || !Array.isArray(result.applications)) {
      throw new Error("Processor scope mismatch.");
    }
    if (getAccessToken() === token) setQueue(result.applications);
  }, [authorized, processor?.id, token]);

  useEffect(() => {
    let live = true;
    setQueue([]);
    if (authorized && processor) {
      refreshQueue().catch(() => {
        if (live) setError("Processor queue unavailable.");
      });
    }
    return () => { live = false; };
  }, [authorized, processor?.id, refreshQueue]);

  async function submit(event) {
    event.preventDefault();
    if (!authorized || !family || !consent || pending) return;
    const key = submissionKey || crypto.randomUUID();
    setSubmissionKey(key);
    setPending(true);
    setError("");
    setNotice("");
    try {
      const result = await sgoRequest("/family/submit/", {
        method: "POST", data: {
          program_id: family.id, grade_level: grade,
          consent: true, consent_version: family.consent_version, submission_key: key,
        },
      });
      if (getAccessToken() !== token || result.application?.program_id !== family.id) return;
      setApplication(result.application);
      setCorrectionGrade(result.application.grade_level);
      setFamilies((previous) => previous.map((item) =>
        item.id === family.id ? { ...item, application_id: result.application.id } : item));
      setSubmissionKey("");
      setNotice("Saved. The submitted fictional application was read back from the server.");
    } catch {
      if (getAccessToken() === token) {
        setError("Submission not confirmed. Retry with the same idempotency key or reload.");
      }
    } finally {
      if (getAccessToken() === token) setPending(false);
    }
  }

  async function correct(event) {
    event.preventDefault();
    if (!authorized || !application || pending) return;
    const key = correctionKey || crypto.randomUUID();
    setCorrectionKey(key);
    setPending(true);
    setError("");
    setNotice("");
    try {
      const result = await sgoRequest(
        "/family/applications/" + encodeURIComponent(application.id) + "/correct/",
        { method: "POST", data: {
          expected_revision: application.revision, grade_level: correctionGrade, correction_key: key,
        }},
      );
      if (getAccessToken() !== token || result.application?.program_id !== family?.id) return;
      setApplication(result.application);
      setCorrectionKey("");
      setNotice("Correction saved and resubmitted for partner review.");
    } catch {
      if (getAccessToken() === token) setError("Correction not confirmed. Reload to check revision before retry.");
    } finally {
      if (getAccessToken() === token) setPending(false);
    }
  }

  async function requestCorrection(item) {
    if (!authorized || !processor || pending) return;
    const key = processorKey || crypto.randomUUID();
    setProcessorKey(key);
    setPending(true);
    setError("");
    setNotice("");
    try {
      const result = await sgoRequest(
        "/processor/applications/" + encodeURIComponent(item.id) + "/request-correction/",
        { method: "POST", data: {
          expected_revision: item.revision, reason, request_key: key,
        }},
      );
      if (getAccessToken() !== token || result.application?.program_id !== processor.id) return;
      setProcessorKey("");
      await refreshQueue();
      setNotice("Nonbinding verification correction request recorded. No award decision was made.");
    } catch {
      if (getAccessToken() === token) {
        setError("Correction request not confirmed. Refresh the queue before retrying.");
      }
    } finally {
      if (getAccessToken() === token) setPending(false);
    }
  }

  return <CrownLayout title="Jireh SGO | Fictional Application Intake"
    subtitle="Local sandbox only — partner SGOs retain program and award authority">
    <p role="note">Synthetic records only. No live family information, documents, eligibility decisions,
      donor funds, scholarships, or payments.</p>
    <p><a href="/jireh-sgo">Return to SGO overview</a></p>
    {!local && <p role="alert">The fictional intake workflow is disabled outside the local demo.</p>}
    {local && !token && <p role="alert">Sign in with a synthetic family or processor account.</p>}
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {local && token && !authorized && !error && <p role="status">Verifying fictional program grants…</p>}
    {authorized && <>
      <section style={card} aria-label="Family application">
        <h3>1. Family: select an authorized partner program</h3>
        {families.length === 0 ? <p>No fictional family grants. SGO membership does not confer family access.</p> : <>
          <label htmlFor="family-program">Partner SGO and program</label>{" "}
          <select id="family-program" value={familyProgram}
            onChange={(e) => { setFamilyProgram(e.target.value); setConsent(false); setError(""); }}>
            {families.map((p) => <option key={p.id} value={p.id}>
              {p.organization} — {p.name} ({p.calendar_year})
            </option>)}
          </select>
          {family && <p>Program policy: {family.policy_version}. Consent version: {family.consent_version}.</p>}
          {family && !family.application_id && !application && <form onSubmit={submit}>
            <label htmlFor="sgo-grade">Fictional grade level</label>{" "}
            <select id="sgo-grade" value={grade} onChange={(e) => {
              setGrade(e.target.value); setSubmissionKey("");
            }}>
              {grades.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
            <p><label><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
              {" "}I consent to submitting this fictional application to the selected partner SGO
              under the displayed demo consent version.</label></p>
            <button type="submit" disabled={!consent || pending}>Submit fictional application</button>
          </form>}
          {application?.program_id === family?.id && <div>
            <h4>Persistent application readback</h4>
            <p>Application: <code>{application.id}</code></p>
            <p>Status: <strong>{application.status}</strong>; revision: {application.revision};
              grade: {application.grade_level}</p>
            <p>Consent recorded: {application.consented_at}</p>
            {application.status === "CORRECTION_REQUESTED" && <form onSubmit={correct}>
              <p>Processor requested: {application.correction_reason}. No partner decision has been issued.</p>
              <label htmlFor="correct-grade">Correct or confirm fictional grade</label>{" "}
              <select id="correct-grade" value={correctionGrade}
                onChange={(e) => { setCorrectionGrade(e.target.value); setCorrectionKey(""); }}>
                {grades.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>{" "}
              <button type="submit" disabled={pending}>Save correction and resubmit</button>
            </form>}
            <button type="button" onClick={() => sgoRequest(
              "/family/applications/" + encodeURIComponent(application.id) + "/",
            ).then((response) => {
              if (getAccessToken() === token && response.application?.program_id === family.id) {
                setApplication(response.application);
                setCorrectionGrade(response.application.grade_level);
              }
            }).catch(() => setError("Readback unavailable."))}>Reload saved application</button>
          </div>}
        </>}
      </section>
      <section style={card} aria-label="Processor verification queue">
        <h3>2. Delegated processor: verification and corrections</h3>
        {processors.length === 0 ? <p>No delegated processor assignment. SGO ADMIN/REVIEWER is not a processor grant.</p> : <>
          <label htmlFor="processor-program">Assigned partner program</label>{" "}
          <select id="processor-program" value={processorProgram}
            onChange={(e) => { setProcessorProgram(e.target.value); setProcessorKey(""); }}>
            {processors.map((p) => <option key={p.id} value={p.id}>{p.organization} — {p.name}</option>)}
          </select>{" "}
          <button type="button" onClick={() => refreshQueue().catch(() => setError("Queue unavailable."))}>
            Refresh queue
          </button>
          <p>Scope: verification support only. No award, eligibility determination, or disbursement authority.</p>
          <label htmlFor="sgo-reason">Non-sensitive correction reason</label>{" "}
          <select id="sgo-reason" value={reason} onChange={(e) => { setReason(e.target.value); setProcessorKey(""); }}>
            {reasons.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          {queue.length === 0 ? <p>No submitted fictional applications in this program.</p> : <table>
            <thead><tr><th scope="col">Application</th><th scope="col">Grade</th>
              <th scope="col">Status</th><th scope="col">Revision</th><th scope="col">Action</th></tr></thead>
            <tbody>{queue.map((item) => <tr key={item.id}>
              <td><code>{item.id.slice(0, 8)}…</code></td>
              <td>{item.grade_level}</td><td>{item.status}</td><td>{item.revision}</td>
              <td><button type="button" disabled={pending || item.status === "CORRECTION_REQUESTED"}
                onClick={() => requestCorrection(item)}>Request correction</button></td>
            </tr>)}</tbody>
          </table>}
        </>}
      </section>
    </>}
  </CrownLayout>;
}

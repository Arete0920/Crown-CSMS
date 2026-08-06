import { useState } from "react";
import {
  getSandboxLoginHref,
  getSandboxPersona,
  getSandboxSchool,
  getSandboxTrack,
  getTrackPersonas,
  getTrackSchools,
} from "./sandboxExperience";
import { recordSandboxEvent, submitSandboxFeedback } from "./sandboxApi";

function getStoredCommandCenter() {
  try {
    return JSON.parse(sessionStorage.getItem("crown.sandbox.command_center") || "{}");
  } catch {
    return {};
  }
}

function getQueryContext() {
  const params = new URLSearchParams(globalThis.location?.search || "");
  const stored = getStoredCommandCenter();

  const track = getSandboxTrack(params.get("experience") || stored?.track || "school");
  const persona = getSandboxPersona(params.get("role") || stored?.persona?.key || localStorage.getItem("crown.demo.role") || "school_admin");
  const school = getSandboxSchool(params.get("school") || stored?.school?.key || stored?.school?.id || persona.defaultSchoolId);
  const guidance = params.get("guidance") || stored?.guidance || localStorage.getItem("crown.demo.guidance") || "guided";
  const tour = params.get("tour") || stored?.tour || persona.tourTitle;
  return { track, persona, school, guidance, tour };
}

export default function SandboxCommandCenter({ compact = false }) {
  const { track, persona, school, guidance, tour } = getQueryContext();
  const personas = getTrackPersonas(track.key);
  const schools = getTrackSchools(track.key);
  const guided = guidance !== "self-guided";
  const steps = Array.isArray(persona.steps) ? persona.steps : [];
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const Container = compact ? "section" : "main";
  const Heading = compact ? "h2" : "h1";

  async function handleFeedbackSubmit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setFeedbackStatus("");

    try {
      await submitSandboxFeedback({
        track: track.key,
        guidance,
        persona: persona.value,
        school: school.key,
        scenario: tour,
        rating: form.get("rating") || "clear",
        note: form.get("note") || "",
        follow_up_requested: form.get("follow_up_requested") === "on",
      });
      setFeedbackStatus("Feedback submitted.");
      setShowFeedback(false);
    } catch (error) {
      setFeedbackStatus(error.message || "Feedback failed.");
    }
  }

  function handleFeedbackClick() {
    recordSandboxEvent({
      event: "feedback_requested",
      track: track.key,
      guidance,
      persona: persona.value,
      school: school.key,
      tour,
    });
    setShowFeedback((value) => !value);
  }

  return (
    <>
      <style>{`
        .sandbox-command-center { border: 1px solid var(--crown-compat-color-3ad3168e09); background: var(--crown-compat-color-f2074b6cef); border-radius: 18px; box-shadow: 0 10px 28px var(--crown-compat-color-09e540a84f); padding: ${compact ? "14px" : "18px"}; margin: ${compact ? "10px 0" : "18px 0"}; color: var(--crown-compat-color-58a558915f); font-family: var(--crown-font); }
        .sandbox-command-header { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 12px; }
        .sandbox-command-title { font-weight: 900; font-size: ${compact ? "16px" : "20px"}; margin: 0; }
        .sandbox-command-badge { border-radius: 999px; border: 1px solid var(--crown-compat-color-9d2fa2fa45); background: var(--crown-compat-color-166130d001); color: var(--crown-compat-color-905109969a); padding: 5px 10px; font-size: 12px; font-weight: 800; white-space: nowrap; }
        .sandbox-command-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }
        .sandbox-command-field { border: 1px solid var(--crown-compat-color-54c30687fc); border-radius: 12px; padding: 10px; background: var(--crown-compat-color-2c1d554440); }
        .sandbox-command-label { color: var(--crown-compat-color-7beae9beff); font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
        .sandbox-command-value { color: var(--crown-compat-color-58a558915f); font-size: 13px; font-weight: 800; }
        .sandbox-command-steps { margin: 12px 0; padding-left: 20px; color: var(--crown-compat-color-7691aaa644); line-height: 1.45; }
        .sandbox-command-steps li:first-child { font-weight: 900; color: var(--crown-compat-color-58a558915f); }
        .sandbox-command-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .sandbox-command-actions a, .sandbox-command-actions button { border: 1px solid var(--crown-compat-color-80e0759046); background: var(--crown-compat-color-f2074b6cef); color: var(--crown-compat-color-21b23e7ef3); border-radius: 10px; padding: 9px 11px; font-size: 13px; font-weight: 800; text-decoration: none; cursor: pointer; }
        .sandbox-command-actions a.primary { background: linear-gradient(120deg, var(--crown-compat-color-f4ce79ce58) 0%, var(--crown-compat-color-550e1aa105) 100%); color: var(--crown-compat-color-f2074b6cef); border: 0; }
        .sandbox-command-warning { border: 1px solid var(--crown-compat-color-acec48178c); background: var(--crown-compat-color-cdf53bae31); color: var(--crown-compat-color-1588a009e3); border-radius: 12px; padding: 10px 12px; font-size: 12px; font-weight: 800; line-height: 1.4; margin-top: 12px; }
        .sandbox-feedback-form { margin-top: 12px; border: 1px solid var(--crown-compat-color-3ad3168e09); border-radius: 14px; padding: 12px; background: var(--crown-compat-color-2c1d554440); display: grid; gap: 10px; }
        .sandbox-feedback-form textarea, .sandbox-feedback-form select { width: 100%; border: 1px solid var(--crown-compat-color-80e0759046); border-radius: 10px; padding: 9px; font: inherit; }
        @media (max-width: 760px) { .sandbox-command-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        @media (max-width: 520px) { .sandbox-command-grid { grid-template-columns: 1fr; } .sandbox-command-header { display: grid; } }
      `}</style>

      <Container className="sandbox-command-center" aria-label="Sandbox command center">
        <div className="sandbox-command-header">
          <div>
            <Heading className="sandbox-command-title">{guided ? "Guided proof path" : "Self-guided sandbox"}</Heading>
            <div className="sandbox-command-value">{tour}</div>
          </div>
          <span className="sandbox-command-badge">Demo Data</span>
        </div>

        <div className="sandbox-command-grid">
          <div className="sandbox-command-field"><div className="sandbox-command-label">Track</div><div className="sandbox-command-value">{track.label}</div></div>
          <div className="sandbox-command-field"><div className="sandbox-command-label">Scenario</div><div className="sandbox-command-value">{school.archetype}</div></div>
          <div className="sandbox-command-field"><div className="sandbox-command-label">Role</div><div className="sandbox-command-value">{persona.label}</div></div>
          <div className="sandbox-command-field"><div className="sandbox-command-label">Organization</div><div className="sandbox-command-value">{school.name}</div></div>
        </div>

        {guided ? (
          <ol className="sandbox-command-steps">{steps.map((step) => <li key={step}>{step}</li>)}</ol>
        ) : (
          <p className="sandbox-command-value">Explore freely. Every page should retain clear role, track, organization, and demo-data context.</p>
        )}

        <div className="sandbox-command-actions">
          <a className="primary" href="/sandbox">Switch track</a>
          {personas.slice(0, 4).map((entry) => (
            <a key={entry.value} href={getSandboxLoginHref(entry.value, school.id, track.key, guidance)}>
              {entry.value === "school_admin" ? (entry.loginLabel || entry.label) : entry.label}
            </a>
          ))}
          {schools.slice(0, 3).map((entry) => (
            <a key={entry.key} href={getSandboxLoginHref(persona.value, entry.id, track.key, guidance)}>{entry.name}</a>
          ))}
          <button type="button" onClick={handleFeedbackClick}>Send feedback</button>
        </div>

        {showFeedback && (
          <form className="sandbox-feedback-form" onSubmit={handleFeedbackSubmit}>
            <label>
              <span>Rating</span>{" "}
              <select name="rating" defaultValue="clear">
                <option value="clear">Clear</option>
                <option value="unclear">Unclear</option>
                <option value="not_relevant">Not relevant</option>
                <option value="blocked">Blocked</option>
              </select>
            </label>
            <label>
              <span>Note</span>{" "}
              <textarea name="note" rows="3" placeholder="Do not enter real student, family, financial, health, safety, or disciplinary data." />
            </label>
            <label>
              <input type="checkbox" name="follow_up_requested" /> Follow-up requested
            </label>
            <button type="submit">Submit feedback</button>
          </form>
        )}

        {feedbackStatus && <div className="sandbox-command-value">{feedbackStatus}</div>}

        <div className="sandbox-command-warning">
          Demo data only. Do not enter real student, child, camper, family, staff, financial, health, safety, or disciplinary records.
        </div>
      </Container>
    </>
  );
}

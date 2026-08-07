import { useState } from "react";
import { Link } from "react-router";
import CrownLogo from "../components/brand/CrownLogo";
import CrownIcon from "../components/icons/CrownIcon.jsx";
import {
  getSandboxLoginHref,
  getSandboxPersona,
  getSandboxSchool,
  getSandboxTrack,
  getTrackPersonas,
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

  const proofContent = (
    <>
      <section className="sandbox-section">
        <div className="sandbox-section-heading">
          <span><CrownIcon name="dashboard" size={18} /></span>
          <div>
            <h2>Current proof context</h2>
            <p>Heritage Christian Academy remains fixed while you review permitted role proof paths.</p>
          </div>
        </div>
        <div className="sandbox-scenario-grid">
          <article className="sandbox-scenario-card">
            <strong>Track</strong>
            <p>{track.label}</p>
          </article>
          <article className="sandbox-scenario-card">
            <strong>Scenario</strong>
            <p>{school.archetype}</p>
          </article>
          <article className="sandbox-scenario-card">
            <strong>Role</strong>
            <p>{persona.label}</p>
          </article>
          <article className="sandbox-scenario-card">
            <strong>Organization</strong>
            <p>{school.name}</p>
          </article>
        </div>
      </section>

      <section className="sandbox-section">
        <div className="sandbox-section-heading">
          <span><CrownIcon name={guided ? "reports" : "control"} size={18} /></span>
          <div>
            <h2>{guided ? "Recommended proof path" : "Self-guided exploration"}</h2>
            <p>{guided ? "Follow the role-specific sequence below." : "Explore freely while preserving the current Heritage role context."}</p>
          </div>
        </div>
        <div className="sandbox-workspace-preview">
          <CrownIcon name={guided ? "reports" : "control"} size={24} />
          <div>
            <strong>{tour}</strong>
            {guided ? (
              <ol>{steps.map((step) => <li key={step}>{step}</li>)}</ol>
            ) : (
              <p>Explore freely. Every page should retain clear role, track, organization, and demo-data context.</p>
            )}
          </div>
        </div>
      </section>

      <section className="sandbox-section">
        <div className="sandbox-section-heading">
          <span><CrownIcon name="user" size={18} /></span>
          <div>
            <h2>Change proof-path role</h2>
            <p>Review another role's proof context here, then return to the evaluator to launch its protected workspace.</p>
          </div>
        </div>
        <div className="sandbox-persona-grid">
          {personas.map((entry) => (
            <Link
              className="sandbox-choice-card launch-hero-action-btn"
              key={entry.value}
              to={getSandboxLoginHref(entry.value, track.key, guidance)}
            >
              <CrownIcon name="user" size={22} />
              <strong>{entry.value === "school_admin" ? (entry.loginLabel || entry.label) : entry.label}</strong>
              <span>{entry.value === persona.value ? "Current proof context" : "Load this role's proof path"}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="sandbox-section">
        <div className="sandbox-section-heading">
          <span><CrownIcon name="control" size={18} /></span>
          <div>
            <h2>Evaluator controls</h2>
            <p>Return to the public evaluator or send feedback about this proof path.</p>
          </div>
        </div>
        <div className="sandbox-choice-grid sandbox-mode-grid">
          <Link className="sandbox-choice-card launch-hero-action-btn is-selected" to="/sandbox">
            <CrownIcon name="dashboard" size={22} />
            <strong>Return to evaluator</strong>
            <span>Choose guidance or another permitted role, then launch its protected CROWN workspace.</span>
          </Link>
          <button type="button" className="sandbox-choice-card" onClick={handleFeedbackClick}>
            <CrownIcon name="chat" size={22} />
            <strong>Send feedback</strong>
            <span>Rate this proof path or request follow-up without entering protected client data.</span>
          </button>
        </div>

        {showFeedback && (
          <form className="sandbox-scenario-card" onSubmit={handleFeedbackSubmit} aria-label="Sandbox feedback">
            <label>
              <strong>Rating</strong>{" "}
              <select name="rating" defaultValue="clear">
                <option value="clear">Clear</option>
                <option value="unclear">Unclear</option>
                <option value="not_relevant">Not relevant</option>
                <option value="blocked">Blocked</option>
              </select>
            </label>
            <label>
              <strong>Note</strong>{" "}
              <textarea name="note" rows="3" placeholder="Do not enter real student, family, financial, health, safety, or disciplinary data." />
            </label>
            <label>
              <input type="checkbox" name="follow_up_requested" /> Follow-up requested
            </label>
            <button type="submit" className="sandbox-launch-button">Submit feedback</button>
          </form>
        )}

        {feedbackStatus && <div className="sandbox-message is-info">{feedbackStatus}</div>}
      </section>

      <div className="sandbox-message is-warning">
        Demo data only. Do not enter real student, child, camper, family, staff, financial, health, safety, or disciplinary records.
      </div>
    </>
  );

  if (compact) {
    return (
      <Container className="sandbox-command-center sandbox-experience-panel" aria-label="Sandbox command center">
        <div className="sandbox-section-heading">
          <span><CrownIcon name="control" size={18} /></span>
          <div>
            <Heading>{guided ? "Guided proof path" : "Self-guided sandbox"}</Heading>
            <p>{tour}</p>
          </div>
        </div>
        {proofContent}
      </Container>
    );
  }

  return (
    <Container className="sandbox-command-center sandbox-experience" aria-label="Sandbox command center">
      <header className="sandbox-experience-header">
        <CrownLogo placement="loginBrand" className="sandbox-experience-logo" />
        <div className="sandbox-experience-header-copy">
          <span className="sandbox-experience-kicker">Heritage Sandbox Command Center</span>
          <Heading>{guided ? "Guided proof path" : "Self-guided sandbox"}</Heading>
          <p>{tour}</p>
        </div>
        <div className="sandbox-experience-trust" aria-label="Sandbox command center safeguards">
          <span><CrownIcon name="shield" size={18} /> Demo data only</span>
          <span><CrownIcon name="school" size={18} /> Heritage Christian Academy</span>
          <span><CrownIcon name="user" size={18} /> {persona.label}</span>
        </div>
      </header>

      <div className="sandbox-experience-layout">
        <aside className="sandbox-experience-steps" aria-label="Current demonstration context">
          <div className="sandbox-step is-active">
            <span>1</span>
            <div><strong>{persona.label}</strong><small>{track.label}</small></div>
          </div>
          <div className="sandbox-step">
            <span>2</span>
            <div><strong>{guided ? "Guided" : "Self-guided"}</strong><small>{tour}</small></div>
          </div>
          <div className="sandbox-step">
            <span>3</span>
            <div><strong>Heritage only</strong><small>School context stays fixed throughout the demonstration.</small></div>
          </div>
          <div className="sandbox-workspace-preview">
            <CrownIcon name="dashboard" size={24} />
            <div>
              <strong>Protected demo workspace</strong>
              <p>Use only fictional demonstration records. Protected role workspaces are launched from the public evaluator.</p>
            </div>
          </div>
        </aside>

        <section className="sandbox-experience-panel" aria-label="Current sandbox proof path">
          {proofContent}
        </section>
      </div>
    </Container>
  );
}

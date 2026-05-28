import {
  getSandboxLoginHref,
  getSandboxPersona,
  getSandboxSchool,
  getSandboxTrack,
  getTrackPersonas,
  getTrackSchools,
} from "./sandboxExperience";
import { recordSandboxEvent } from "./sandboxTelemetry";

function getQueryContext() {
  const params = new URLSearchParams(globalThis.location?.search || "");
  const track = getSandboxTrack(params.get("experience") || "school");
  const persona = getSandboxPersona(params.get("role") || localStorage.getItem("crown.demo.role") || "school_admin");
  const school = getSandboxSchool(params.get("school") || persona.defaultSchoolId);
  const guidance = params.get("guidance") || "guided";
  const tour = params.get("tour") || persona.tourTitle;
  return { track, persona, school, guidance, tour };
}

export default function SandboxCommandCenter({ compact = false }) {
  const { track, persona, school, guidance, tour } = getQueryContext();
  const personas = getTrackPersonas(track.key);
  const schools = getTrackSchools(track.key);
  const guided = guidance !== "self-guided";
  const steps = Array.isArray(persona.steps) ? persona.steps : [];

  function handleFeedbackClick() {
    recordSandboxEvent("feedback_requested", {
      track: track.key,
      guidance,
      persona: persona.value,
      school: school.key,
      tour,
    });
  }

  return (
    <>
      <style>{`
        .sandbox-command-center {
          border: 1px solid #d6e2ee;
          background: #ffffff;
          border-radius: 18px;
          box-shadow: 0 10px 28px rgba(11, 29, 49, 0.12);
          padding: ${compact ? "14px" : "18px"};
          margin: ${compact ? "10px 0" : "18px 0"};
          color: #102843;
          font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .sandbox-command-header {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .sandbox-command-title {
          font-weight: 900;
          font-size: ${compact ? "16px" : "20px"};
          margin: 0;
        }

        .sandbox-command-badge {
          border-radius: 999px;
          border: 1px solid #c8daf5;
          background: #edf4ff;
          color: #183a63;
          padding: 5px 10px;
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .sandbox-command-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin: 12px 0;
        }

        .sandbox-command-field {
          border: 1px solid #e1e9f2;
          border-radius: 12px;
          padding: 10px;
          background: #f8fbff;
        }

        .sandbox-command-label {
          color: #5b6e83;
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          margin-bottom: 3px;
        }

        .sandbox-command-value {
          color: #102843;
          font-size: 13px;
          font-weight: 800;
        }

        .sandbox-command-steps {
          margin: 12px 0;
          padding-left: 20px;
          color: #304a63;
          line-height: 1.45;
        }

        .sandbox-command-steps li:first-child {
          font-weight: 900;
          color: #102843;
        }

        .sandbox-command-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 12px;
        }

        .sandbox-command-actions a,
        .sandbox-command-actions button {
          border: 1px solid #c9d7e6;
          background: #ffffff;
          color: #183556;
          border-radius: 10px;
          padding: 9px 11px;
          font-size: 13px;
          font-weight: 800;
          text-decoration: none;
          cursor: pointer;
        }

        .sandbox-command-actions a.primary {
          background: linear-gradient(120deg, #12345a 0%, #1e4a7a 100%);
          color: #ffffff;
          border: 0;
        }

        .sandbox-command-warning {
          border: 1px solid #c6a54a;
          background: #fbf6e8;
          color: #7a5317;
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 12px;
          font-weight: 800;
          line-height: 1.4;
          margin-top: 12px;
        }

        @media (max-width: 760px) {
          .sandbox-command-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 520px) {
          .sandbox-command-grid {
            grid-template-columns: 1fr;
          }

          .sandbox-command-header {
            display: grid;
          }
        }
      `}</style>

      <section className="sandbox-command-center" aria-label="Sandbox command center">
        <div className="sandbox-command-header">
          <div>
            <h2 className="sandbox-command-title">{guided ? "Guided proof path" : "Self-guided sandbox"}</h2>
            <div className="sandbox-command-value">{tour}</div>
          </div>
          <span className="sandbox-command-badge">Demo Data</span>
        </div>

        <div className="sandbox-command-grid">
          <div className="sandbox-command-field">
            <div className="sandbox-command-label">Track</div>
            <div className="sandbox-command-value">{track.label}</div>
          </div>
          <div className="sandbox-command-field">
            <div className="sandbox-command-label">Scenario</div>
            <div className="sandbox-command-value">{school.archetype}</div>
          </div>
          <div className="sandbox-command-field">
            <div className="sandbox-command-label">Role</div>
            <div className="sandbox-command-value">{persona.label}</div>
          </div>
          <div className="sandbox-command-field">
            <div className="sandbox-command-label">Organization</div>
            <div className="sandbox-command-value">{school.name}</div>
          </div>
        </div>

        {guided ? (
          <ol className="sandbox-command-steps">
            {steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        ) : (
          <p className="sandbox-command-value">
            Explore freely. The checklist is available when needed, but every page should retain clear role, track,
            organization, and demo-data context.
          </p>
        )}

        <div className="sandbox-command-actions">
          <a className="primary" href="/sandbox">Switch track</a>
          {personas.slice(0, 4).map((entry) => (
            <a key={entry.value} href={getSandboxLoginHref(entry.value, school.id, track.key, guidance)}>
              {entry.label}
            </a>
          ))}
          {schools.slice(0, 3).map((entry) => (
            <a key={entry.key} href={getSandboxLoginHref(persona.value, entry.id, track.key, guidance)}>
              {entry.name}
            </a>
          ))}
          <button type="button" onClick={handleFeedbackClick}>Send feedback</button>
        </div>

        <div className="sandbox-command-warning">
          Demo data only. Do not enter real student, child, camper, family, staff, financial, health, safety, or disciplinary records.
        </div>
      </section>
    </>
  );
}

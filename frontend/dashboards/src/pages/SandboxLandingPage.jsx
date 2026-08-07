import { useEffect, useMemo, useState } from "react";
import CrownLogo from "../components/brand/CrownLogo";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownIcon from "../components/icons/CrownIcon.jsx";
import {
  SANDBOX_TRACKS,
  getSandboxSchool,
  getTrackPersonas,
  getTrackSchools,
} from "../sandbox/sandboxExperience";
import {
  createSandboxSession,
  recordSandboxEvent,
  resolveSandboxInvite,
  storeSandboxSession,
} from "../sandbox/sandboxApi";

function getInitialInvite() {
  const params = new URLSearchParams(globalThis.location?.search || "");
  return params.get("invite") || "";
}

export default function SandboxLandingPage() {
  const [selectedTrackKey, setSelectedTrackKey] = useState("school");
  const [selectedMode, setSelectedMode] = useState("guided");
  const [inviteId] = useState(getInitialInvite);
  const [invite, setInvite] = useState(null);
  const [inviteError, setInviteError] = useState("");
  const [launchingRole, setLaunchingRole] = useState("");
  const [launchError, setLaunchError] = useState("");

  const selectedTrack = useMemo(
    () => SANDBOX_TRACKS.find((track) => track.key === selectedTrackKey) || SANDBOX_TRACKS[0],
    [selectedTrackKey]
  );
  const trackSchools = useMemo(() => getTrackSchools(selectedTrack.key), [selectedTrack.key]);
  const personas = useMemo(() => getTrackPersonas(selectedTrack.key), [selectedTrack.key]);
  const defaultSchool = getSandboxSchool(selectedTrack.primarySchoolKey);

  useEffect(() => {
    if (!inviteId) return;
    resolveSandboxInvite(inviteId)
      .then((resolved) => {
        setInvite(resolved);
        if (resolved?.track) setSelectedTrackKey(resolved.track);
        if (resolved?.default_guidance) setSelectedMode(resolved.default_guidance);
      })
      .catch((error) => setInviteError(error.message || "Invite could not be resolved."));
  }, [inviteId]);

  async function launchPersona(persona) {
    setLaunchError("");
    setLaunchingRole(persona.value);

    try {
      const session = await createSandboxSession({
        inviteId,
        role: persona.value,
        school: defaultSchool.key || defaultSchool.id,
        track: selectedTrack.key,
        guidance: selectedMode,
        tour: persona.tourTitle,
      });

      storeSandboxSession(session);

      await recordSandboxEvent({
        event: "sandbox_persona_launched",
        invite_id: inviteId || null,
        track: selectedTrack.key,
        guidance: selectedMode,
        persona: persona.value,
        school: defaultSchool.key || defaultSchool.id,
        tour: persona.tourTitle,
        route: session.route,
      });

      const targetRoute = session.route || persona.route || "/school-admin-dashboard";
      if (typeof globalThis.location?.assign === "function") {
        globalThis.location.assign(targetRoute);
      }
    } catch (error) {
      setLaunchError(error.message || "Sandbox launch failed.");
      setLaunchingRole("");
    }
  }

  const visiblePersonas = invite?.allowed_roles?.length
    ? personas.filter((persona) => invite.allowed_roles.includes(persona.value))
    : personas;

  return (
    <CrownLayout mainClassName="sandbox-crown-layout">
      <div className="sandbox-experience">
        <header className="sandbox-experience-header">
          <CrownLogo placement="loginBrand" className="sandbox-experience-logo" />
          <div className="sandbox-experience-header-copy">
            <span className="sandbox-experience-kicker" role="heading" aria-level="2">Guided Proof Sandbox</span>
            <h1>See the real CROWN workspace with safe fictional data.</h1>
            <p>
              Choose a school scenario and role. CROWN will create a protected demo session and open the same
              sidebar, dashboard blocks, workflows, and module surfaces used by client schools.
            </p>
          </div>
          <div className="sandbox-experience-trust" aria-label="Sandbox safeguards">
            <span><CrownIcon name="shield" size={18} /> Demo data only</span>
            <span><CrownIcon name="user" size={18} /> No buyer password</span>
            <span><CrownIcon name="dashboard" size={18} /> Real role workspace</span>
          </div>
        </header>

        <div className="sandbox-experience-layout">
          <aside className="sandbox-experience-steps" aria-label="Demonstration steps">
            <div className="sandbox-step is-active"><span>1</span><div><strong>Choose the track</strong><small>Select the client scenario.</small></div></div>
            <div className="sandbox-step"><span>2</span><div><strong>Choose guidance</strong><small>Use a guided or independent path.</small></div></div>
            <div className="sandbox-step"><span>3</span><div><strong>Launch a role</strong><small>Enter the actual CROWN workspace.</small></div></div>
            <div className="sandbox-workspace-preview">
              <CrownIcon name="dashboard" size={24} />
              <div>
                <strong>What opens next</strong>
                <p>Role-aware sidebar, operational cards, queues, alerts, reports, and connected module actions.</p>
              </div>
            </div>
          </aside>

          <section className="sandbox-experience-panel" aria-label="Sandbox launcher">
            {invite ? <div className="sandbox-message is-info">Invite loaded for {invite.organization_label}. Access is limited to approved roles and demo scenarios.</div> : null}
            {inviteError ? <div className="sandbox-message is-error">{inviteError}</div> : null}
            {launchError ? <div className="sandbox-message is-error">{launchError}</div> : null}

            <section className="sandbox-section">
              <div className="sandbox-section-heading"><span>1</span><div><h2>Pick a demo track</h2><p>Choose the school or ministry context you want to demonstrate.</p></div></div>
              <div className="sandbox-choice-grid sandbox-track-grid">
                {SANDBOX_TRACKS.map((track) => (
                  <button
                    type="button"
                    key={track.key}
                    className={`sandbox-choice-card ${track.key === selectedTrack.key ? "is-selected" : ""}`}
                    onClick={() => setSelectedTrackKey(track.key)}
                    disabled={Boolean(invite?.track && invite.track !== track.key)}
                  >
                    <CrownIcon name="school" size={22} />
                    <strong>{track.label}</strong>
                    <span>{track.summary}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="sandbox-section">
              <div className="sandbox-section-heading"><span>2</span><div><h2>Choose the demonstration style</h2><p>Guided is recommended for a first owner walkthrough.</p></div></div>
              <div className="sandbox-choice-grid sandbox-mode-grid">
                <button type="button" className={`sandbox-choice-card ${selectedMode === "guided" ? "is-selected" : ""}`} onClick={() => setSelectedMode("guided")}>
                  <CrownIcon name="reports" size={22} />
                  <strong>Guided path</strong>
                  <span>CROWN explains the story and presents the next recommended action.</span>
                </button>
                <button type="button" className={`sandbox-choice-card ${selectedMode === "self-guided" ? "is-selected" : ""}`} onClick={() => setSelectedMode("self-guided")}>
                  <CrownIcon name="control" size={22} />
                  <strong>Self-guided exploration</strong>
                  <span>Move independently through the available role workspace and modules.</span>
                </button>
              </div>
            </section>

            <section className="sandbox-section">
              <div className="sandbox-section-heading"><span>3</span><div><h2>Start as a role</h2><p>The role launch creates a protected demo session before opening the dashboard.</p></div></div>
              <div className="sandbox-persona-grid">
                {visiblePersonas.map((persona) => (
                  <article className="sandbox-persona-card persona-card" key={persona.value}>
                    <div className="sandbox-persona-icon"><CrownIcon name="user" size={22} /></div>
                    <div><strong>{persona.label}</strong><p>{persona.promise}</p></div>
                    <button
                      type="button"
                      className="sandbox-launch-button"
                      disabled={Boolean(launchingRole)}
                      onClick={() => launchPersona(persona)}
                    >
                      {launchingRole === persona.value ? "Launching..." : `Start ${selectedMode === "guided" ? "guided" : "self-guided"}`}
                    </button>
                  </article>
                ))}
              </div>
            </section>

            <section className="sandbox-section sandbox-scenarios">
              <div className="sandbox-section-heading"><span><CrownIcon name="school" size={18} /></span><div><h2>Included {selectedTrack.label.toLowerCase()} scenarios</h2><p>All records are fictional and isolated from client data.</p></div></div>
              <div className="sandbox-scenario-grid">
                {trackSchools.map((school) => (
                  <article className="sandbox-scenario-card" key={school.key}>
                    <strong>{school.name}</strong>
                    <p>{school.archetype}. Best for {school.bestFor}.</p>
                    <span>{school.enrollment} demo records</span>
                  </article>
                ))}
              </div>
            </section>

            <div className="sandbox-message is-warning">
              Demo data only. Do not enter real student, camper, child, family, staff, financial, health, safety, or disciplinary records.
            </div>
          </section>
        </div>
      </div>
    </CrownLayout>
  );
}

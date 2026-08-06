import { useEffect, useMemo, useState } from "react";
import CrownLogo from "../components/brand/CrownLogo";
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
    <>
      <style>{`
        .sandbox-root { min-height: 100vh; font-family: var(--crown-font); background: linear-gradient(150deg, var(--crown-compat-color-202a5f0a18) 0%, var(--crown-compat-color-2c1d554440) 72%); color: var(--crown-compat-color-bcb7254751); }
        .sandbox-hero { display: grid; grid-template-columns: minmax(300px, 0.9fr) minmax(320px, 1.1fr); gap: 32px; max-width: 1180px; margin: 0 auto; padding: 42px 24px 28px; align-items: center; }
        .sandbox-brand-card { border-radius: 28px; background: radial-gradient(130% 130% at 10% 20%, var(--crown-compat-color-550e1aa105) 0%, var(--crown-compat-color-3fe2c08e8f) 72%); color: white; min-height: 560px; padding: 34px; box-shadow: 0 18px 46px var(--crown-compat-color-57b27ef25d); display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; position: relative; }
        .sandbox-logo-wrap { max-width: 260px; margin-bottom: 44px; }
        .sandbox-brand-card h1 { font-family: var(--crown-font); font-size: clamp(36px, 5vw, 58px); line-height: 1.02; margin: 0 0 16px; }
        .sandbox-brand-card p { color: var(--crown-compat-color-43e3474ee6); font-size: 17px; line-height: 1.55; margin: 0; max-width: 520px; }
        .sandbox-proof-pills { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
        .sandbox-pill { border: 1px solid var(--crown-compat-color-2bfbe87360); background: var(--crown-compat-color-c34f5a2a4d); border-radius: 999px; padding: 8px 12px; font-size: 13px; font-weight: 700; color: var(--crown-compat-color-c801d51c67); }
        .sandbox-panel { background: white; border: 1px solid var(--crown-compat-color-523c4be52b); border-radius: 24px; box-shadow: 0 14px 38px var(--crown-compat-color-09e540a84f); padding: 28px; }
        .sandbox-kicker { display: inline-flex; border-radius: 999px; background: var(--crown-compat-color-166130d001); border: 1px solid var(--crown-compat-color-9d2fa2fa45); color: var(--crown-compat-color-905109969a); padding: 6px 12px; font-size: 12px; font-weight: 800; letter-spacing: 0.2px; margin-bottom: 14px; }
        .sandbox-panel h2 { font-family: var(--crown-font); font-size: 34px; line-height: 1.15; margin: 0 0 10px; color: var(--crown-compat-color-8e47de7f3c); }
        .sandbox-panel p { color: var(--crown-compat-color-fff712ee45); line-height: 1.55; margin: 0 0 18px; }
        .track-grid, .mode-grid, .persona-grid, .school-grid { display: grid; gap: 12px; }
        .track-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
        .mode-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 18px 0; }
        .persona-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 14px; }
        .school-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 16px; }
        .select-card, .persona-card, .school-card { border: 1px solid var(--crown-compat-color-3ad3168e09); border-radius: 16px; background: var(--crown-compat-color-f2074b6cef); padding: 14px; text-align: left; color: var(--crown-compat-color-62760b63ce); }
        button.select-card, button.persona-card { cursor: pointer; }
        .select-card.active { border-color: var(--crown-compat-color-550e1aa105); box-shadow: 0 0 0 3px var(--crown-compat-color-49c00fe872); background: var(--crown-compat-color-1eceb30284); }
        .card-title { font-weight: 800; margin-bottom: 4px; }
        .card-copy { font-size: 13px; color: var(--crown-compat-color-b1be72453d); line-height: 1.4; }
        .persona-card { display: grid; gap: 10px; }
        .primary-link { display: inline-flex; justify-content: center; align-items: center; border-radius: 10px; background: linear-gradient(120deg, var(--crown-compat-color-f4ce79ce58) 0%, var(--crown-compat-color-550e1aa105) 100%) !important; color: white !important; -webkit-text-fill-color: white !important; text-decoration: none; padding: 10px 12px; font-weight: 800; font-size: 14px; border: 0; cursor: pointer; }
        .primary-link[disabled] { opacity: 0.62; cursor: wait; }
        .sandbox-warning, .sandbox-error, .sandbox-invite { margin-top: 18px; padding: 12px 14px; border-radius: 14px; font-weight: 800; font-size: 13px; line-height: 1.45; }
        .sandbox-warning { border: 1px solid var(--crown-compat-color-acec48178c); background: var(--crown-compat-color-cdf53bae31); color: var(--crown-compat-color-1588a009e3); }
        .sandbox-error { border: 1px solid var(--crown-compat-color-05f1c462d9); background: var(--crown-compat-color-bba72e0781); color: var(--crown-compat-color-0dcdbfad72); }
        .sandbox-invite { border: 1px solid var(--crown-compat-color-9d2fa2fa45); background: var(--crown-compat-color-166130d001); color: var(--crown-compat-color-905109969a); }
        .section-title { margin: 22px 0 8px; font-weight: 900; color: var(--crown-compat-color-58a558915f); }
        @media (max-width: 980px) { .sandbox-hero { grid-template-columns: 1fr; } .sandbox-brand-card { min-height: auto; } }
        @media (max-width: 720px) { .track-grid, .mode-grid, .persona-grid, .school-grid { grid-template-columns: 1fr; } }
      `}</style>

      <main className="sandbox-root">
        <section className="sandbox-hero">
          <aside className="sandbox-brand-card" aria-label="CROWN sandbox overview">
            <div>
              <div className="sandbox-logo-wrap">
                <CrownLogo placement="loginBrand" />
              </div>
              <h1>Guided Proof Sandbox</h1>
              <p>
                Explore CROWN with safe fictional data. Choose the market track, choose the level of guidance,
                then enter the product through a one-click role-specific proof path.
              </p>
              <div className="sandbox-proof-pills">
                <span className="sandbox-pill">One-click role launch</span>
                <span className="sandbox-pill">No buyer passwords</span>
                <span className="sandbox-pill">Guided or self-guided</span>
                <span className="sandbox-pill">Demo data only</span>
              </div>
            </div>
            <p>CROWN - Christian School Management Solution</p>
          </aside>

          <section className="sandbox-panel" aria-label="Sandbox launcher">
            <span className="sandbox-kicker">Safe Demo Environment</span>
            <h2>Choose how you want to evaluate CROWN.</h2>
            <p>
              Start guided when evaluating for the first time. Use self-guided when you already understand the story and
              want to explore modules on your own.
            </p>

            {invite && <div className="sandbox-invite">Invite loaded for {invite.organization_label}. Access is limited to approved roles and demo scenarios.</div>}
            {inviteError && <div className="sandbox-error">{inviteError}</div>}
            {launchError && <div className="sandbox-error">{launchError}</div>}

            <div className="section-title">1. Pick a demo track</div>
            <div className="track-grid">
              {SANDBOX_TRACKS.map((track) => (
                <button
                  type="button"
                  key={track.key}
                  className={`select-card ${track.key === selectedTrack.key ? "active" : ""}`}
                  onClick={() => setSelectedTrackKey(track.key)}
                  disabled={Boolean(invite?.track && invite.track !== track.key)}
                >
                  <div className="card-title">{track.label}</div>
                  <div className="card-copy">{track.summary}</div>
                </button>
              ))}
            </div>

            <div className="section-title">2. Pick guided or self-guided</div>
            <div className="mode-grid">
              <button type="button" className={`select-card ${selectedMode === "guided" ? "active" : ""}`} onClick={() => setSelectedMode("guided")}>
                <div className="card-title">Guided path</div>
                <div className="card-copy">Best for first-time buyers. CROWN tells the story and shows the next step.</div>
              </button>
              <button type="button" className={`select-card ${selectedMode === "self-guided" ? "active" : ""}`} onClick={() => setSelectedMode("self-guided")}>
                <div className="card-title">Self-guided exploration</div>
                <div className="card-copy">Best after a short intro. The user can move through modules independently.</div>
              </button>
            </div>

            <div className="section-title">3. Start as a role</div>
            <div className="persona-grid">
              {visiblePersonas.map((persona) => (
                <div className="persona-card" key={persona.value}>
                  <div>
                    <div className="card-title">{persona.label}</div>
                    <div className="card-copy">{persona.promise}</div>
                  </div>
                  <button
                    type="button"
                    className="primary-link"
                    disabled={Boolean(launchingRole)}
                    onClick={() => launchPersona(persona)}
                  >
                    {launchingRole === persona.value
                      ? "Launching..."
                      : `Start ${selectedMode === "guided" ? "guided" : "self-guided"}`}
                  </button>
                </div>
              ))}
            </div>

            <div className="section-title">Included {selectedTrack.label.toLowerCase()} scenarios</div>
            <div className="school-grid">
              {trackSchools.map((school) => (
                <div className="school-card" key={school.key}>
                  <div className="card-title">{school.name}</div>
                  <div className="card-copy">
                    {school.archetype}. Best for {school.bestFor}. Seed size: {school.enrollment} demo records.
                  </div>
                </div>
              ))}
            </div>

            <div className="sandbox-warning">
              Demo data only. Do not enter real student, camper, child, family, staff, financial, health, safety, or disciplinary records.
            </div>
          </section>
        </section>
      </main>
    </>
  );
}

import { useEffect, useState } from "react";
import { loadParentJourneyOverview } from "./parentJourneyState.js";

function formatMoney(cents) {
  if (typeof cents !== "number" || Number.isNaN(cents)) {
    return "Unavailable";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function formatDateTime(value) {
  if (!value) return "Not set";

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function sectionTitle(focus) {
  switch (focus) {
    case "billing":
      return "Billing readiness";
    case "aid":
      return "Financial aid preparation";
    default:
      return "Parent lifecycle status";
  }
}

function sectionSubtitle(focus) {
  switch (focus) {
    case "billing":
      return "Contract and deposit readiness are read from the parent overview contract.";
    case "aid":
      return "Aid intent, awards, and sync state are read from the parent overview contract.";
    default:
      return "Household, application, checklist, and activation state are read from the parent overview contract.";
  }
}

function HighlightCard({ label, value, helper }) {
  return (
    <article className="learning-workflow-metric crown-tone-royal">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}

function ApplicationCard({ application, focus }) {
  const focusDetails = focus === "billing"
    ? [
        { label: "Contract", value: application.contract_status || "unknown" },
        { label: "Deposit", value: application.deposit_status || "unknown" },
        { label: "Payment precheck", value: application.payment_precheck?.status || "pending" },
      ]
    : focus === "aid"
      ? [
          { label: "Aid status", value: application.financial_aid_status || "unknown" },
          { label: "Awards", value: String(application.aid_award_count ?? 0) },
          { label: "Aid sync", value: application.aid_contract_sync_status || "unknown" },
        ]
      : [
          { label: "Lifecycle", value: application.lifecycle_stage || "unknown" },
          { label: "Checklist", value: application.checklist_summary?.missing_count === 0 ? "Complete" : "In progress" },
          { label: "Parent portal", value: application.parent_portal_activation_status || "unknown" },
        ];

  return (
    <article className="learning-record-detail-card">
      <p className="crown-eyebrow">{application.application_status || "Application"}</p>
      <h2>{application.parent_status || application.lifecycle_stage || "Parent lifecycle"}</h2>
      <div className="learning-record-detail-block">
        <strong>Next action</strong>
        <p>{application.next_action || "No next action listed."}</p>
      </div>
      <div className="learning-record-detail-block">
        <strong>Checklist</strong>
        <p>
          {application.checklist_summary?.missing_count ?? 0} missing of {application.checklist_summary?.required_total ?? 0} required items.
        </p>
      </div>
      <div className="learning-record-detail-block">
        <strong>Opened</strong>
        <p>{formatDateTime(application.submitted_at)}</p>
      </div>
      <div className="learning-authority-grid" style={{ marginTop: 16 }}>
        {focusDetails.map((item) => (
          <article key={item.label}>
            <strong>{item.label}</strong>
            <p>{item.value}</p>
          </article>
        ))}
      </div>
    </article>
  );
}

export default function ParentJourneyOverviewPage({ focus = "status" }) {
  const [state, setState] = useState({ status: "loading", overview: null, errorMessage: "" });

  useEffect(() => {
    let active = true;

    setState({ status: "loading", overview: null, errorMessage: "" });

    loadParentJourneyOverview()
      .then((overview) => {
        if (!active) return;
        setState({ status: "ready", overview, errorMessage: "" });
      })
      .catch((error) => {
        if (!active) return;
        setState({
          status: "error",
          overview: null,
          errorMessage: error instanceof Error ? error.message : String(error),
        });
      });

    return () => {
      active = false;
    };
  }, [focus]);

  if (state.status === "loading") {
    return (
      <main className="crown-dashboard learning-workflow-page">
        <section className="crown-dashboard-status-card" aria-busy="true">
          Loading parent journey contract…
        </section>
      </main>
    );
  }

  if (state.status === "error" || !state.overview) {
    return (
      <main className="crown-dashboard learning-workflow-page">
        <section className="crown-dashboard-status-card">
          <span className="crown-status-label">Parent journey unavailable</span>
          <strong>Backend contract could not be loaded</strong>
          <small>{state.errorMessage || "No overview returned."}</small>
        </section>
      </main>
    );
  }

  const overview = state.overview;
  const continuity = overview.admissions_continuity || {};
  const applications = Array.isArray(continuity.applications) ? continuity.applications : [];
  const summary = continuity.summary || {};
  const household = overview.household || {};

  const firstApplication = applications[0] || {};
  const metrics = [
    {
      label: "Children",
      value: String(overview.children_count ?? 0),
      helper: "Household students currently surfaced in the parent overview.",
    },
    {
      label: "Missing work",
      value: String(overview.missing_assignments_total ?? 0),
      helper: "Outstanding assignments or checklist items.",
    },
    {
      label: "Upcoming work",
      value: String(overview.upcoming_assignments_total ?? 0),
      helper: "Near-term assignments or child responsibilities.",
    },
    {
      label: "Household balance",
      value: formatMoney(household.balance_cents),
      helper: "Open balance read from the parent overview contract.",
    },
  ];

  const callout = focus === "billing"
    ? {
        label: "Billing summary",
        value: summary.contract_complete > 0 ? "Contract complete" : "Action needed",
        helper: `Accepted pending contract: ${summary.accepted_pending_contract ?? 0}; deposit complete: ${summary.deposit_complete ?? 0}.`,
      }
    : focus === "aid"
      ? {
          label: "Aid summary",
          value: firstApplication.financial_aid_status || "Not started",
          helper: `Awards: ${firstApplication.aid_award_count ?? 0}; contract sync: ${firstApplication.aid_contract_sync_status || "unknown"}.`,
        }
      : {
          label: "Lifecycle summary",
          value: String(summary.total ?? applications.length),
          helper: `Applications surfaced: ${summary.total ?? applications.length}.`,
        };

  return (
    <main className="crown-dashboard learning-workflow-page" data-testid={`parent-journey-${focus}`}>
      <header className="crown-dashboard-hero">
        <div>
          <p className="crown-eyebrow">Parent360 source of truth</p>
          <h1>{sectionTitle(focus)}</h1>
          <p className="crown-dashboard-purpose">{sectionSubtitle(focus)}</p>

          <div className="learning-authority-strip">
            <span>Household: {household.name || "Current family"}</span>
            <span>Applications: {String(summary.total ?? applications.length)}</span>
          </div>
        </div>

        <aside className="crown-dashboard-status-card">
          <span className="crown-status-label">Focus</span>
          <strong>{callout.label}</strong>
          <small>{callout.helper}</small>
        </aside>
      </header>

      <section className="learning-workflow-metrics" aria-label="Parent journey metrics">
        {metrics.map((metric) => (
          <HighlightCard key={metric.label} {...metric} />
        ))}
      </section>

      <section className="learning-authority-card" aria-label="Parent journey summary">
        <div className="crown-section-heading">
          <div>
            <p className="crown-eyebrow">Contract summary</p>
            <h2>Read from the parent overview contract</h2>
          </div>
        </div>

        <div className="learning-authority-grid">
          <article>
            <strong>Accepted pending contract</strong>
            <p>{String(summary.accepted_pending_contract ?? 0)}</p>
          </article>
          <article>
            <strong>Contract complete</strong>
            <p>{String(summary.contract_complete ?? 0)}</p>
          </article>
          <article>
            <strong>Deposit complete</strong>
            <p>{String(summary.deposit_complete ?? 0)}</p>
          </article>
        </div>
      </section>

      <section className="learning-record-detail-grid" aria-label="Applications">
        {applications.length > 0 ? applications.map((application) => (
          <ApplicationCard application={application} focus={focus} key={application.application_id} />
        )) : (
          <article className="learning-record-detail-card">
            <p className="crown-eyebrow">No applications</p>
            <h2>Parent overview returned no applications</h2>
            <p>The contract is loaded, but the household has no application records yet.</p>
          </article>
        )}
      </section>
    </main>
  );
}

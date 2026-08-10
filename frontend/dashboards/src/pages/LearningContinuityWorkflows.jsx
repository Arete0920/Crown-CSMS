import { useEffect, useMemo, useState } from "react";
import "../features/dashboards/crown-dashboard.css";
import "./LearningContinuityWorkflows.css";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import TeacherLessonPlanPage from "./TeacherLessonPlanPage.jsx";
import { loadLearningContinuityPage } from "../features/learningContinuity/learningContinuityApi.js";
import { getLearningContinuityTruth } from "../features/learningContinuity/learningContinuityTruth.js";

function toneClass(tone) {
  return `crown-tone-${tone ?? "royal"}`;
}

function MetricCard({ metric }) {
  return (
    <article className={`learning-workflow-metric ${toneClass(metric.tone)}`}>
      <span>{metric.label}</span>
      <strong>{metric.value}</strong>
      <p>{metric.helper}</p>
    </article>
  );
}

function AuthorityRules({ rules }) {
  return (
    <section className="learning-authority-card" aria-label="CROWN authority rules">
      <div className="crown-section-heading">
        <div>
          <p className="crown-eyebrow">Authority model</p>
          <h2>CROWN is the source of truth</h2>
        </div>
      </div>
      <div className="learning-authority-grid">
        {rules.map((rule) => (
          <article key={rule.rule}>
            <strong>{rule.rule}</strong>
            <p>{rule.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function WorkflowSection({ title, items }) {
  return (
    <article className="learning-workflow-section-card">
      <h2>{title}</h2>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </article>
  );
}

function SourceRecordTable({ records }) {
  return (
    <section className="learning-workflow-table-wrap" aria-label="CROWN source records">
      <div className="crown-section-heading">
        <div><p className="crown-eyebrow">CROWN records</p><h2>Authoritative process and data records</h2></div>
      </div>
      <div className="learning-record-table">
        <div className="learning-record-row learning-record-head">
          <span>CROWN ID</span><span>Record type</span><span>State</span><span>Sync</span><span>Next action</span>
        </div>
        {records.map((record) => (
          <div className="learning-record-row" key={record.crownRecordId}>
            <strong>{record.crownRecordId}</strong><span>{record.recordType}</span><span>{record.state}</span><span>{record.syncState}</span><small>{record.nextAction}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function RecordDetailGrid({ records }) {
  return (
    <section className="learning-record-detail-grid" aria-label="Record authority details">
      {records.map((record) => (
        <article className="learning-record-detail-card" key={`${record.crownRecordId}-detail`}>
          <p className="crown-eyebrow">{record.recordType}</p><h2>{record.crownRecordId}</h2>
          <div className="learning-record-detail-block"><strong>CROWN truth</strong><p>{record.crownTruth}</p></div>
          <div className="learning-record-detail-block"><strong>External role</strong><p>{record.microsoftRole}</p></div>
        </article>
      ))}
    </section>
  );
}

function WorkflowList({ workflow }) {
  return (
    <section className="learning-authority-card" aria-label="Workflow sequence">
      <div className="crown-section-heading"><div><p className="crown-eyebrow">CROWN workflow</p><h2>Process sequence</h2></div></div>
      <ol className="learning-workflow-ordered-list">{workflow.map((item) => <li key={item}>{item}</li>)}</ol>
    </section>
  );
}

function LearningWorkflowPage({ pageKey }) {
  const fallbackPage = useMemo(() => getLearningContinuityTruth(pageKey), [pageKey]);
  const [payload, setPayload] = useState({ mode: "loading", authorityRules: [], page: fallbackPage, pageKey });

  useEffect(() => {
    let active = true;
    loadLearningContinuityPage(pageKey).then((loadedPayload) => {
      if (active) setPayload({ ...loadedPayload, pageKey });
    });
    return () => { active = false; };
  }, [pageKey, fallbackPage]);

  const { page, authorityRules, mode } = payload;
  const isStale = payload.pageKey !== pageKey;
  const statusDetail = payload.statusDetail ?? "API data is used when available. Fixture data keeps the page functional while backend and Microsoft adapters are built.";

  return (
    <CrownLayout>
      <main className="crown-dashboard learning-workflow-page" data-testid={`learning-workflow-${pageKey}`}>
        <header className="crown-dashboard-hero">
          <div>
            <p className="crown-eyebrow">{page.eyebrow}</p><h1>{page.title}</h1><p className="crown-dashboard-purpose">{page.subtitle}</p>
            <div className="learning-authority-strip"><span>Primary source: {page.primarySource}</span><span>Owner: {page.crownOwner}</span></div>
            <p className="learning-authority-statement">{page.authorityStatement}</p>
          </div>
          <aside className="crown-dashboard-status-card"><span className="crown-status-label">Data mode</span><strong>{isStale ? "loading" : mode}</strong><small>{statusDetail}</small></aside>
        </header>
        <section className="learning-workflow-metrics" aria-label="Workflow metrics">{page.metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}</section>
        <AuthorityRules rules={authorityRules} />
        <section className="learning-workflow-section-grid" aria-label="Workflow responsibilities">
          <WorkflowSection title="CROWN owns" items={[page.authorityStatement]} />
          <WorkflowSection title="External systems" items={page.externalSystems} />
          <WorkflowSection title="Required workflow" items={page.workflow} />
        </section>
        <SourceRecordTable records={page.records} /><RecordDetailGrid records={page.records} /><WorkflowList workflow={page.workflow} />
      </main>
    </CrownLayout>
  );
}

export function OnlineLearningCommandCenter() { return <LearningWorkflowPage pageKey="onlineCommand" />; }

// The teacher cockpit is intentionally transactional: both /teacher/daily-cockpit and
// /teacher/lesson-plans/today now open the persisted lesson-plan editor rather than a tour page.
export function TeacherDailyCockpitPage() { return <TeacherLessonPlanPage />; }

export function ParentLearningStatusPage() { return <LearningWorkflowPage pageKey="parentStatus" />; }
export function StudentTodayPage() { return <LearningWorkflowPage pageKey="studentToday" />; }
export function CurriculumImportPage() { return <LearningWorkflowPage pageKey="curriculumImport" />; }
export function MicrosoftEducationHealthPage() { return <LearningWorkflowPage pageKey="microsoftHealth" />; }
export function DualEnrollmentTrackerPage() { return <LearningWorkflowPage pageKey="dualEnrollment" />; }
export function InterventionCoursesPage() { return <LearningWorkflowPage pageKey="interventions" />; }

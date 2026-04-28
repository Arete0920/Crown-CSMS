import "../styles/admin-command-center.css";
import CrownLayout from "../components/crown/CrownLayout";

const executiveKpis = [
  {
    label: "Total Students",
    value: "1,248",
    detail: "+4.1% enrollment growth",
    tone: "blue",
    icon: "👥",
  },
  {
    label: "Faculty & Staff",
    value: "156",
    detail: "3 onboarding this week",
    tone: "indigo",
    icon: "🏫",
  },
  {
    label: "Attendance Rate",
    value: "96.2%",
    detail: "Above benchmark",
    tone: "emerald",
    icon: "✅",
  },
  {
    label: "Tuition Collected",
    value: "$2.4M",
    detail: "94% of term target",
    tone: "gold",
    icon: "💳",
  },
  {
    label: "Open Admissions",
    value: "42",
    detail: "12 tours scheduled",
    tone: "sky",
    icon: "📝",
  },
  {
    label: "Active Alerts",
    value: "6",
    detail: "2 require today",
    tone: "rose",
    icon: "⚠️",
  },
];

const modules = [
  {
    title: "Admissions / Enrollment",
    badge: "42 open",
    main: "18 applications ready",
    detail: "Tours, applications, packets, and family follow-up",
    tone: "blue",
    metrics: [
      ["New inquiries", "64"],
      ["Applications", "42"],
      ["Tours scheduled", "12"],
      ["Packets pending", "9"],
    ],
    actions: ["Review applications", "Schedule tour", "Send packet"],
  },
  {
    title: "Attendance",
    badge: "On track",
    main: "96.2% present",
    detail: "Daily attendance, absences, late arrivals, missing submissions",
    tone: "emerald",
    metrics: [
      ["Present today", "96.2%"],
      ["Absent", "31"],
      ["Late arrivals", "12"],
      ["Missing submissions", "3"],
    ],
    actions: ["Open attendance", "Notify families", "Export report"],
  },
  {
    title: "Academics / Gradebook",
    badge: "Review",
    main: "18 students at risk",
    detail: "Academic risk, missing grades, assignment completion, report cards",
    tone: "indigo",
    metrics: [
      ["Missing grades", "7"],
      ["At-risk students", "18"],
      ["Assignments complete", "91%"],
      ["Reports ready", "84%"],
    ],
    actions: ["Review gradebook", "Academic risk list", "Progress reports"],
  },
  {
    title: "Finance / Billing",
    badge: "Strong",
    main: "$2.4M collected",
    detail: "Tuition, balances, payment plans, aid queue, batch status",
    tone: "gold",
    metrics: [
      ["Collected", "$2.4M"],
      ["Outstanding", "$148K"],
      ["Payment plans", "37"],
      ["Aid pending", "11"],
    ],
    actions: ["Review billing", "Process batch", "Aid queue"],
  },
  {
    title: "Communications",
    badge: "Needs replies",
    main: "8 family replies",
    detail: "Announcements, staff messages, family responses, approvals",
    tone: "sky",
    metrics: [
      ["Pending replies", "8"],
      ["Scheduled", "3"],
      ["Unread staff", "3"],
      ["Drafts", "2"],
    ],
    actions: ["Send announcement", "Message center", "Review replies"],
  },
  {
    title: "Staff / HR",
    badge: "Coverage",
    main: "2 substitutes needed",
    detail: "Coverage, certifications, HR tasks, onboarding, staff readiness",
    tone: "slate",
    metrics: [
      ["Staff present", "148"],
      ["Subs needed", "2"],
      ["Certs expiring", "5"],
      ["HR tasks", "7"],
    ],
    actions: ["Staff roster", "Review coverage", "HR checklist"],
  },
  {
    title: "Student Life / Discipline",
    badge: "Follow up",
    main: "10 follow-ups",
    detail: "Behavior alerts, discipline cases, service hours, counseling",
    tone: "rose",
    metrics: [
      ["Discipline", "10"],
      ["Referrals", "4"],
      ["Service hours", "23"],
      ["Behavior alerts", "6"],
    ],
    actions: ["Student life queue", "Discipline cases", "Service hours"],
  },
  {
    title: "Health / Safety",
    badge: "Attention",
    main: "14 medical forms",
    detail: "Nurse visits, incident reports, contacts, safety readiness",
    tone: "emerald",
    metrics: [
      ["Nurse visits", "9"],
      ["Forms missing", "14"],
      ["Incidents", "2"],
      ["Contacts incomplete", "8"],
    ],
    actions: ["Health office", "Review incidents", "Emergency contacts"],
  },
  {
    title: "Calendar / Events",
    badge: "This week",
    main: "11 events",
    detail: "Events, rooms, field trips, volunteers, approvals",
    tone: "blue",
    metrics: [
      ["Events", "11"],
      ["Trips pending", "3"],
      ["Rooms booked", "18"],
      ["Volunteers needed", "6"],
    ],
    actions: ["Create event", "Review calendar", "Approve trip"],
  },
  {
    title: "System / IT",
    badge: "Healthy",
    main: "0 failed syncs",
    detail: "Integrations, tickets, backups, syncs, platform health",
    tone: "indigo",
    metrics: [
      ["System", "Healthy"],
      ["Failed syncs", "0"],
      ["Tickets", "5"],
      ["Backup", "Current"],
    ],
    actions: ["System integrity", "Sync errors", "Contact support"],
  },
];

const priorities = [
  "Approve 4 enrollment packets",
  "Review 3 attendance exceptions",
  "Sign off tuition adjustment queue",
  "Confirm substitute coverage",
  "Publish parent newsletter",
];

const rightRail = {
  prayer: [
    "Mrs. Carter surgery recovery",
    "6th grade retreat travel safety",
    "New families joining this week",
  ],
  announcements: [
    "Chapel Friday at 9:00 AM",
    "Re-enrollment packets due Monday",
    "Parent newsletter scheduled",
  ],
  calendar: [
    ["8:15 AM", "Leadership huddle"],
    ["10:00 AM", "Admissions tour"],
    ["1:30 PM", "Finance review"],
    ["3:15 PM", "Staff briefing"],
  ],
  communications: [
    "8 family replies need response",
    "3 unread staff messages",
    "2 announcement drafts pending approval",
  ],
  alerts: [
    "Two attendance submissions missing",
    "Financial aid queue due today",
    "Emergency contacts incomplete",
  ],
};

function ToneDot({ tone }) {
  return <span className={`admin-command-dot admin-command-dot-${tone}`} aria-hidden="true" />;
}

function KpiCard({ item }) {
  return (
    <article className={`admin-command-kpi admin-command-kpi-${item.tone}`}>
      <div>
        <p className="admin-command-eyebrow">{item.label}</p>
        <strong>{item.value}</strong>
        <span>{item.detail}</span>
      </div>
      <div className="admin-command-kpi-icon" aria-hidden="true">
        {item.icon}
      </div>
    </article>
  );
}

function ModuleCard({ module }) {
  return (
    <article className={`admin-command-module admin-command-module-${module.tone}`}>
      <header>
        <div>
          <p className="admin-command-eyebrow">{module.title}</p>
          <h3>{module.main}</h3>
        </div>
        <span className="admin-command-badge">{module.badge}</span>
      </header>

      <p className="admin-command-module-detail">{module.detail}</p>

      <div className="admin-command-metric-pairs">
        {module.metrics.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <footer>
        {module.actions.map((action) => (
          <button key={action} type="button">
            {action}
          </button>
        ))}
      </footer>
    </article>
  );
}

function RightRailCard({ title, children, accent = "blue" }) {
  return (
    <section className={`admin-command-rail-card admin-command-rail-card-${accent}`}>
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default function AdminCommandCenterDashboard() {
  return (
    <CrownLayout>
      <main className="admin-command-page" data-testid="admin-command-center">
        <section className="admin-command-hero">
          <div>
            <p className="admin-command-eyebrow">CROWN Launch Preview</p>
            <h1>Good morning, Sarah!</h1>
            <p>Heritage Christian Academy</p>
          </div>

          <div className="admin-command-hero-actions">
            <span>Sandbox preview data shown. Connect backend for live records.</span>
            <button type="button">Generate report</button>
          </div>
        </section>

      <section className="admin-command-layout">
        <div className="admin-command-main">
          <section className="admin-command-kpi-grid" aria-label="Executive KPIs">
            {executiveKpis.map((item) => (
              <KpiCard key={item.label} item={item} />
            ))}
          </section>

          <section className="admin-command-priority-panel">
            <div>
              <p className="admin-command-eyebrow">Today’s Priorities</p>
              <h2>Administrator action queue</h2>
              <p>High-value items requiring leadership decision or follow-up.</p>
            </div>

            <ul>
              {priorities.map((priority) => (
                <li key={priority}>
                  <ToneDot tone="gold" />
                  <span>{priority}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="admin-command-section-header">
            <div>
              <p className="admin-command-eyebrow">Operational Command Grid</p>
              <h2>Run the school from one screen</h2>
            </div>
            <span>10 active operating areas</span>
          </section>

          <section className="admin-command-module-grid" aria-label="Operational Modules">
            {modules.map((module) => (
              <ModuleCard key={module.title} module={module} />
            ))}
          </section>

          <section className="admin-command-bottom-grid">
            <article className="admin-command-chart-card">
              <div>
                <p className="admin-command-eyebrow">Enrollment Trend</p>
                <h3>Steady growth across the school year</h3>
              </div>
              <div className="admin-command-chart">
                <svg viewBox="0 0 720 220" role="img" aria-label="Enrollment trend line chart">
                  <defs>
                    <linearGradient id="crownLine" x1="0" x2="1">
                      <stop offset="0%" stopColor="#2563eb" />
                      <stop offset="100%" stopColor="#fbbf24" />
                    </linearGradient>
                  </defs>
                  {[40, 80, 120, 160, 200].map((y) => (
                    <line key={y} x1="30" x2="700" y1={y} y2={y} className="grid" />
                  ))}
                  <polyline
                    points="40,164 150,154 260,142 370,134 480,128 590,124 690,118"
                    fill="none"
                    stroke="url(#crownLine)"
                    strokeWidth="5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {[40, 150, 260, 370, 480, 590, 690].map((x, index) => {
                    const ys = [164, 154, 142, 134, 128, 124, 118];
                    return <circle key={x} cx={x} cy={ys[index]} r="7" />;
                  })}
                </svg>
              </div>
            </article>

            <article className="admin-command-readiness-card">
              <div>
                <p className="admin-command-eyebrow">Department Readiness</p>
                <h3>Today’s cross-team snapshot</h3>
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Area</th>
                    <th>Owner</th>
                    <th>Status</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Admissions", "Registrar", "Applications reviewed", "8:10 AM"],
                    ["Attendance", "Student Life", "Homeroom complete", "8:22 AM"],
                    ["Finance", "Business Office", "Batch posted", "9:05 AM"],
                    ["Academics", "Dean", "Risk list updated", "9:20 AM"],
                    ["Communications", "Front Office", "Newsletter queued", "9:42 AM"],
                  ].map(([area, owner, status, updated]) => (
                    <tr key={area}>
                      <td>{area}</td>
                      <td>{owner}</td>
                      <td>{status}</td>
                      <td>{updated}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </article>
          </section>
        </div>

        <aside className="admin-command-rail" aria-label="Administrator context rail">
          <RightRailCard title="Prayer Requests" accent="gold">
            <ul>
              {rightRail.prayer.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </RightRailCard>

          <RightRailCard title="Daily Devotion" accent="blue">
            <blockquote>
              “Trust in the Lord with all your heart and lean not on your own understanding.”
            </blockquote>
            <span>Proverbs 3:5</span>
          </RightRailCard>

          <RightRailCard title="Announcements" accent="sky">
            <ul>
              {rightRail.announcements.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </RightRailCard>

          <RightRailCard title="Today’s Calendar" accent="blue">
            <div className="admin-command-calendar-list">
              {rightRail.calendar.map(([time, item]) => (
                <div key={`${time}-${item}`}>
                  <strong>{time}</strong>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </RightRailCard>

          <RightRailCard title="To-Dos / Approvals" accent="gold">
            <ul>
              {priorities.slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </RightRailCard>

          <RightRailCard title="Communications" accent="sky">
            <ul>
              {rightRail.communications.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </RightRailCard>

          <RightRailCard title="Critical Alerts" accent="rose">
            <ul>
              {rightRail.alerts.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </RightRailCard>
        </aside>
      </section>
      </main>
    </CrownLayout>
  );
}

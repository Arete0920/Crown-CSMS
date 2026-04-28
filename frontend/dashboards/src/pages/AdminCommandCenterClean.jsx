import "../styles/admin-command-center-clean.css";

const navItems = [
  "Overview",
  "Admissions",
  "Attendance",
  "Academics",
  "Finance",
  "Communications",
  "Staff & HR",
  "Student Services",
  "Reports",
  "Settings",
];

const commandCenterLanes = [
  "Enrollment",
  "Attendance",
  "Academics",
  "Finance",
  "Communications",
  "Staff & HR",
  "Student Services",
  "Alerts",
];

const kpis = [
  {
    label: "Total Students",
    value: "912",
    detail: "+18 this month",
    tone: "blue",
  },
  {
    label: "Attendance Today",
    value: "99.1%",
    detail: "Above target",
    tone: "green",
  },
  {
    label: "Open Admissions",
    value: "42",
    detail: "11 need review",
    tone: "purple",
  },
  {
    label: "Tuition Collected",
    value: "$2.4M",
    detail: "94% of target",
    tone: "gold",
  },
  {
    label: "Academic Watch",
    value: "9",
    detail: "Students need support",
    tone: "red",
  },
  {
    label: "Staff Coverage",
    value: "98%",
    detail: "2 substitutes needed",
    tone: "teal",
  },
];

const priorityItems = [
  {
    title: "Finalize enrollment packets",
    detail: "12 applications need principal signoff before end of day.",
    meta: "Due 4:00 PM",
  },
  {
    title: "Resolve attendance exceptions",
    detail: "5 homerooms still missing first-period submission.",
    meta: "In progress",
  },
  {
    title: "Review tuition follow-up queue",
    detail: "3 family accounts require administrator approval.",
    meta: "Finance",
  },
];

const operationalCards = [
  {
    title: "Enrollment Pipeline",
    subtitle: "Admissions and re-enrollment",
    rows: [
      ["New inquiries", "128"],
      ["Applications", "96"],
      ["Interviews scheduled", "24"],
      ["Accepted / pending", "42"],
    ],
  },
  {
    title: "Academic Oversight",
    subtitle: "Grades, progress, and intervention",
    rows: [
      ["Grades needing review", "18"],
      ["Missing assignments", "37"],
      ["Intervention plans", "9"],
      ["Upcoming tests", "12"],
    ],
  },
  {
    title: "Finance Snapshot",
    subtitle: "Tuition, billing, and aid",
    rows: [
      ["Tuition collected", "$2.4M"],
      ["Outstanding balance", "$38.5K"],
      ["Aid reviews", "14"],
      ["Invoices pending", "19"],
    ],
  },
  {
    title: "Communications",
    subtitle: "Families, staff, and announcements",
    rows: [
      ["Unread family messages", "7"],
      ["Draft announcements", "3"],
      ["Staff alerts", "2"],
      ["Newsletter status", "Ready"],
    ],
  },
  {
    title: "Staff & HR",
    subtitle: "Coverage, hiring, and onboarding",
    rows: [
      ["Open requisitions", "3"],
      ["Coverage gaps today", "2"],
      ["Onboarding tasks", "5"],
      ["Evaluations due", "4"],
    ],
  },
  {
    title: "Student Services",
    subtitle: "Counseling, health, and support plans",
    rows: [
      ["Support plans active", "14"],
      ["Counselor follow-ups", "6"],
      ["Health alerts", "2"],
      ["Family conferences", "9"],
    ],
  },
];

const rightRail = [
  {
    title: "Prayer & Devotion",
    body: [
      "Be strong and courageous.",
      "The Lord your God will be with you wherever you go.",
      "Joshua 1:9",
    ],
    tone: "gold",
  },
  {
    title: "Announcements",
    body: [
      "Chapel Friday at 9:00 AM",
      "Re-enrollment packets due Monday",
      "Parent newsletter scheduled",
    ],
    tone: "blue",
  },
  {
    title: "Today’s Calendar",
    body: [
      "8:00 AM — Faculty devotion",
      "9:00 AM — Chapel service",
      "3:30 PM — Teacher meeting",
      "6:00 PM — Board meeting",
    ],
    tone: "blue",
  },
  {
    title: "To-Dos / Approvals",
    body: [
      "4 enrollment decisions",
      "3 tuition follow-ups",
      "2 health record exceptions",
      "1 staff onboarding item",
    ],
    tone: "red",
  },
  {
    title: "Communications",
    body: [
      "7 replies need response",
      "3 unread staff messages",
      "2 drafts pending approval",
    ],
    tone: "green",
  },
  {
    title: "Alerts",
    body: [
      "Bus loop incident follow-up pending",
      "SIS retry threshold nearing limit",
      "Emergency contact completion below target",
    ],
    tone: "red",
  },
];

function Brand() {
  return (
    <div className="clean-brand" aria-label="CROWN brand">
      <img src="/brand/crown-logo-transparent.svg" alt="CROWN logo" />
      <div>
        <strong>School Administrator</strong>
        <span>Command Center</span>
      </div>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="clean-sidebar">
      <Brand />

      <div className="clean-school-pill">
        <span>Heritage Christian Academy</span>
        <b>⌄</b>
      </div>

      <nav className="clean-nav" aria-label="School administrator navigation">
        {navItems.map((item) => (
          <button key={item} type="button" className={item === "Overview" ? "active" : ""}>
            <span>{item}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}

function Topbar() {
  return (
    <header className="clean-topbar">
      <label className="clean-search">
        <span>Search</span>
        <input placeholder="Search students, families, staff, invoices, alerts..." />
      </label>

      <button type="button" className="clean-action">+ Quick Add</button>

      <div className="clean-year">
        <span>School Year</span>
        <strong>2025–2026</strong>
      </div>

      <button type="button" className="clean-icon-button">✉<b>7</b></button>
      <button type="button" className="clean-icon-button">🔔<b>4</b></button>

      <button type="button" className="clean-user">
        <span>SJ</span>
        <div>
          <strong>Sarah James</strong>
          <small>School Administrator</small>
        </div>
      </button>
    </header>
  );
}

function KpiCard({ item }) {
  return (
    <article className={`clean-kpi clean-kpi-${item.tone}`}>
      <span>{item.label}</span>
      <strong>{item.value}</strong>
      <p>{item.detail}</p>
    </article>
  );
}

function PriorityPanel() {
  return (
    <section className="clean-card clean-priorities">
      <div className="clean-section-heading">
        <div>
          <h2>Leadership Priorities</h2>
          <p>Items requiring administrator attention today.</p>
        </div>
        <button type="button">View all</button>
      </div>

      <div className="clean-priority-list">
        {priorityItems.map((item) => (
          <article key={item.title}>
            <div>
              <h3>{item.title}</h3>
              <p>{item.detail}</p>
            </div>
            <strong>{item.meta}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}

function EnrollmentChart() {
  const stages = [
    ["Inquiries", "128", "100%"],
    ["Applications", "96", "75%"],
    ["Interviews", "64", "50%"],
    ["Offers", "48", "38%"],
    ["Enrolled", "32", "25%"],
  ];

  return (
    <section className="clean-card clean-chart-card">
      <div className="clean-section-heading">
        <div>
          <h2>Enrollment Funnel</h2>
          <p>Admissions movement by stage.</p>
        </div>
      </div>

      <div className="clean-funnel">
        {stages.map(([label, value, width]) => (
          <div key={label} className="clean-funnel-row">
            <span>{label}</span>
            <div>
              <i style={{ width }} />
            </div>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function AttendanceChart() {
  return (
    <section className="clean-card clean-chart-card">
      <div className="clean-section-heading">
        <div>
          <h2>Attendance Overview</h2>
          <p>Today’s campus attendance.</p>
        </div>
      </div>

      <div className="clean-attendance-layout">
        <div className="clean-donut">
          <strong>99.1%</strong>
          <span>Present</span>
        </div>

        <div className="clean-legend">
          <div><i className="green" /><span>Present</span><strong>492</strong></div>
          <div><i className="gold" /><span>Tardy</span><strong>6</strong></div>
          <div><i className="red" /><span>Absent</span><strong>14</strong></div>
        </div>
      </div>
    </section>
  );
}

function GradeDistribution() {
  const grades = [
    ["A", "42%", "#2563EB"],
    ["B", "31%", "#14B8A6"],
    ["C", "18%", "#F5B82E"],
    ["D-F", "9%", "#EF4444"],
  ];

  return (
    <section className="clean-card clean-chart-card">
      <div className="clean-section-heading">
        <div>
          <h2>Grade Distribution</h2>
          <p>Current academic performance mix.</p>
        </div>
      </div>

      <div className="clean-grade-bars">
        {grades.map(([label, value, color]) => (
          <div key={label}>
            <span>{label}</span>
            <div><i style={{ width: value, background: color }} /></div>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function OperationalCard({ item }) {
  return (
    <section className="clean-card clean-operational-card">
      <h2>{item.title}</h2>
      <p>{item.subtitle}</p>

      <div>
        {item.rows.map(([label, value]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}

function RightRail() {
  return (
    <aside className="clean-right-rail">
      {rightRail.map((item) => (
        <section key={item.title} className={`clean-rail-card clean-rail-${item.tone}`}>
          <h2>{item.title}</h2>
          <ul>
            {item.body.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      ))}
    </aside>
  );
}

export default function AdminCommandCenterClean() {
  return (
    <div className="clean-admin-shell">
      <Sidebar />

      <div className="clean-admin-body">
        <Topbar />

        <main className="clean-main">
          <section className="clean-content">
            <section className="clean-title-row">
              <div>
                <p>School Administrator Dashboard</p>
                <div className="clean-page-title">CROWN Command Center</div>
              </div>
            </section>

            <section className="clean-hero">
              <div>
                <strong>Good morning, Sarah</strong>
                <span>Focus on enrollment decisions, attendance completion, billing approvals, and family communication.</span>
              </div>
              <blockquote>
                <p>“Commit to the Lord whatever you do, and He will establish your plans.”</p>
                <span>Proverbs 16:3</span>
              </blockquote>
            </section>

            <section className="clean-lanes" aria-label="Command center lanes">
              {commandCenterLanes.map((lane) => (
                <span key={lane}>{lane}</span>
              ))}
            </section>

            <section className="clean-kpi-grid" aria-label="Administrator KPI summary">
              {kpis.map((item) => (
                <KpiCard key={item.label} item={item} />
              ))}
            </section>

            <section className="clean-dashboard-grid">
              <PriorityPanel />
              <EnrollmentChart />
              <AttendanceChart />
              <GradeDistribution />
            </section>

            <section className="clean-operational-grid">
              {operationalCards.map((item) => (
                <OperationalCard key={item.title} item={item} />
              ))}
            </section>
          </section>

          <RightRail />
        </main>
      </div>
    </div>
  );
}

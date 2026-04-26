import "../styles/admin-command-center-final.css";

const kpis = [
  { label: "Total Students", value: "912", detail: "5 new this month", icon: "👥", tone: "blue" },
  { label: "Admissions", value: "418", detail: "9 this month", icon: "👪", tone: "purple" },
  { label: "Attendance Today", value: "99.4%", detail: "Above target", icon: "✓", tone: "green" },
  { label: "Open Invoices", value: "19", detail: "$38,580 outstanding", icon: "$", tone: "gold" },
  { label: "Teacher Attendance", value: "91.1%", detail: "9 Approaching", icon: "◎", tone: "gold" },
  { label: "Monthly Revenue", value: "$128,940", detail: "8.4% over last month", icon: "▥", tone: "green" },
];

const navGroups = [
  { title: "Command Centre", items: ["Dashboard", "Overview"] },
  { title: "School Operations", items: ["Admissions", "Students", "Attendance", "Gradebook", "Academics"] },
  { title: "Offices & Finance", items: ["Finance", "Human Resources", "Boarding"] },
  { title: "Communications", items: ["Communications", "Database", "Administration", "Chaplain"] },
  { title: "Student Services", items: ["Family Pay", "Student Lending", "Fundraising"] },
];

const quickActions = [
  "Add Inquiry",
  "Add Student",
  "Take Attendance",
  "Create Invoice",
  "Send Message",
  "Add Event",
  "Create Announcement",
  "Run Report",
  "Upload Document",
  "More",
];

const rightRail = [
  {
    title: "Daily Prayer & Devotion",
    hasPhoto: true,
    photoLabel: "Morning devotion",
    items: [
      "Be strong and courageous.",
      "Do not be afraid; the Lord your God will be with you.",
      "— Joshua 1:9",
    ],
    action: "Read devotion",
    tone: "devotion",
  },
  {
    title: "Today's Devotion",
    hasPhoto: true,
    photoLabel: "Open Bible",
    items: [
      "Walking by Faith, Not by Sight",
      "Reflect on 2 Corinthians 5:7",
    ],
    action: "Read more",
    tone: "devotion",
  },
  {
    title: "Announcements",
    items: [
      "Spring Carnival is this Saturday",
      "Chapel guest speaker next week",
      "Yearbook orders due May 1",
    ],
    action: "View all",
  },
  {
    title: "Counsel Segment",
    isGrid: true,
    gridRows: [
      ["Student", "Proxy", "Score"],
      ["A. James", "Parent", "92"],
      ["B. Smith", "Counselor", "87"],
      ["C. Brown", "Teacher", "78"],
    ],
    action: "View all",
    tone: "counsel",
  },
  {
    title: "Family Focus",
    items: [
      "3 families awaiting follow-up",
      "1 new inquiry this morning",
      "2 re-enrollment meetings today",
    ],
    action: "View families",
  },
  {
    title: "Today Due",
    items: [
      "Submit payroll approvals",
      "Review 3 pending invoices",
      "Respond to board email",
      "Sign field trip forms",
    ],
    action: "View all tasks",
    tone: "attention",
  },
  {
    title: "System Status",
    items: ["All systems operational", "Last checked: 7:45 AM"],
    action: "View status",
    tone: "system",
  },
];

const overviewCards = [
  {
    title: "Academics Overview",
    rows: [
      ["Assignments due today", "24"],
      ["Grades needing review", "18"],
      ["Missing assignments", "7"],
      ["Upcoming tests", "12"],
    ],
    action: "Go to gradebook",
  },
  {
    title: "Student Demographics",
    rows: [
      ["Elementary K–5", "156"],
      ["Middle School 6–8", "128"],
      ["High School 9–12", "168"],
      ["Pre-K", "60"],
    ],
    action: "View demographic report",
  },
  {
    title: "Grade Distribution",
    rows: [
      ["A (90–100)", "142"],
      ["B (80–89)", "198"],
      ["C (70–79)", "87"],
      ["D / F (below 70)", "23"],
    ],
    action: "View gradebook",
  },
  {
    title: "Staff Overview",
    rows: [
      ["Certified Teachers", "42"],
      ["Support Staff", "18"],
      ["Administrators", "6"],
      ["Substitutes active", "3"],
    ],
    action: "View staff directory",
  },
];

function KpiCard({ item }) {
  return (
    <article className={`cc-kpi cc-tone-${item.tone}`}>
      <div>
        <p>{item.label}</p>
        <strong>{item.value}</strong>
        <span>{item.detail}</span>
      </div>
      <div className="cc-kpi-icon" aria-hidden="true">
        {item.icon}
      </div>
    </article>
  );
}

function NavSidebar() {
  return (
    <>
      <aside className="cc-icon-rail" aria-label="Quick module rail">
        <img src="/brand/crown-mark-transparent.svg" alt="" className="cc-icon-rail-mark" />
        {["⌂", "👥", "▣", "$", "▤", "✉", "✓", "⚙"].map((icon, index) => (
          <button key={icon} className={index === 0 ? "active" : ""} type="button">
            {icon}
          </button>
        ))}
      </aside>

      <aside className="cc-nav" aria-label="Primary CROWN navigation">
        <img
          src="/brand/crown-logo-transparent.svg"
          alt="CROWN Christian School Management Solution"
          className="cc-logo"
        />

        <button className="cc-school-switcher" type="button">
          <span>Heritage Christian Academy</span>
          <span>⌄</span>
        </button>

        <nav>
          {navGroups.map((group) => (
            <section key={group.title}>
              <h2>{group.title}</h2>
              {group.items.map((item) => (
                <a key={item} href="/" className={item === "Dashboard" ? "active" : ""}>
                  <span>{item}</span>
                  <span>›</span>
                </a>
              ))}
            </section>
          ))}
        </nav>

        <div className="cc-school-card">
          <img src="/brand/crown-mark-transparent.svg" alt="" />
          <div>
            <strong>Heritage Christian Academy</strong>
            <span>Est. 1998</span>
          </div>
        </div>
      </aside>
    </>
  );
}

function Topbar() {
  return (
    <header className="cc-topbar">
      <label className="cc-search">
        <span>⌕</span>
        <input placeholder="Search students, families, staff, invoices..." />
      </label>

      <button className="cc-primary-action" type="button">+ Quick Add</button>

      <div className="cc-year">
        <span>School Year</span>
        <strong>2025–2026</strong>
      </div>

      <button type="button" className="cc-top-icon">✉<b>3</b></button>
      <button type="button" className="cc-top-icon">🔔<b>6</b></button>
      <button type="button" className="cc-top-icon">☑</button>
      <button type="button" className="cc-top-icon">?</button>

      <button className="cc-user" type="button">
        <span className="cc-avatar">DA</span>
        <span>
          <strong>David Anderson</strong>
          <small>School Administrator</small>
        </span>
        <span>⌄</span>
      </button>
    </header>
  );
}

function FunnelCard() {
  const levels = [
    ["Inquiries", "128", "cc-blue"],
    ["Applications", "96", "cc-teal"],
    ["Interviews", "64", "cc-purple"],
    ["Offers", "48", "cc-gold"],
    ["Enrolled", "32", "cc-red"],
  ];

  return (
    <article className="cc-card cc-analytics-card">
      <h3>Enrollment Funnel <span>This Year</span></h3>
      <div className="cc-funnel-layout">
        <div className="cc-funnel">
          {levels.map((level, index) => (
            <div key={level[0]} className={`cc-funnel-level ${level[2]}`} style={{ width: `${100 - index * 14}%` }} />
          ))}
        </div>

        <div className="cc-legend">
          {levels.map(([label, value, color]) => (
            <div key={label}>
              <i className={color} />
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
      <a href="/">View full enrollment report →</a>
    </article>
  );
}

function AttendanceCard() {
  return (
    <article className="cc-card cc-analytics-card">
      <h3>Attendance Overview</h3>
      <div className="cc-attendance-layout">
        <div className="cc-donut">
          <span>99.4%</span>
          <small>Today</small>
        </div>
        <div className="cc-legend">
          <div><i className="cc-teal" /><span>Present</span><strong>492</strong></div>
          <div><i className="cc-red" /><span>Absent</span><strong>14</strong></div>
          <div><i className="cc-gold" /><span>Tardy</span><strong>6</strong></div>
        </div>
      </div>
      <a href="/">View attendance dashboard →</a>
    </article>
  );
}

function FinanceCard() {
  return (
    <article className="cc-card cc-analytics-card">
      <h3>Financial Overview <span>This Month</span></h3>
      <div className="cc-finance-summary">
        <div><span>Total Income</span><strong>$128,540</strong></div>
        <div><span>Total Expenses</span><strong>$89,230</strong></div>
        <div><span>Net Income</span><strong className="positive">$39,310</strong></div>
      </div>
      <div className="cc-bars" aria-label="Income and expense chart">
        {Array.from({ length: 26 }).map((_, index) => (
          <div key={index}>
            <i style={{ height: `${35 + ((index * 17) % 95)}px` }} />
            <b style={{ height: `${25 + ((index * 23) % 80)}px` }} />
          </div>
        ))}
      </div>
      <a href="/">View finance dashboard →</a>
    </article>
  );
}

function QuickActions() {
  return (
    <section className="cc-card cc-quick-actions">
      <h3>Quick Actions</h3>
      <div>
        {quickActions.map((action) => (
          <button key={action} type="button">
            <span>+</span>
            {action}
          </button>
        ))}
      </div>
    </section>
  );
}

function SmallCard({ card }) {
  return (
    <article className="cc-card cc-small-card">
      <h3>{card.title}</h3>
      {card.rows.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
      <a href="/">{card.action} →</a>
    </article>
  );
}

function RightRail() {
  return (
    <aside className="cc-right-rail" aria-label="Administrator context rail">
      {rightRail.map((section) => (
        <section key={section.title} className={`cc-rail-card cc-rail-${section.tone || "default"}`}>
          <h3>{section.title}</h3>
          {section.hasPhoto && (
            <div className="cc-rail-photo" role="img" aria-label={section.photoLabel} />
          )}
          {section.isGrid ? (
            <table className="cc-rail-grid">
              <thead>
                <tr>{section.gridRows[0].map((h) => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {section.gridRows.slice(1).map((row) => (
                  <tr key={row[0]}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ul>
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
          <a href="/">{section.action} →</a>
        </section>
      ))}
    </aside>
  );
}

export default function AdminCommandCenterFinal() {
  return (
    <div className="cc-dashboard">
      <NavSidebar />

      <div className="cc-shell">
        <Topbar />

        <main className="cc-main">
          <section className="cc-content">
            <section className="cc-hero">
              <div>
                <h1>Good morning, David! ☀</h1>
                <p>You&apos;re leading with purpose and making an eternal impact every day.</p>
              </div>

              <blockquote>
                &ldquo;Commit to the Lord whatever you do, and He will establish your plans.&rdquo;
                <span>— Proverbs 16:3</span>
              </blockquote>

              <img src="/brand/crown-mark-transparent.svg" alt="" />
            </section>

            <section className="cc-kpi-grid" aria-label="Executive KPI cards">
              {kpis.map((item) => (
                <KpiCard key={item.label} item={item} />
              ))}
            </section>

            <section className="cc-analytics-grid">
              <FunnelCard />
              <AttendanceCard />
              <FinanceCard />
            </section>

            <QuickActions />

            <section className="cc-small-grid">
              {overviewCards.map((card) => (
                <SmallCard key={card.title} card={card} />
              ))}
            </section>

            <section className="cc-bottom-grid">
              <SmallCard card={{
                title: "School Year Progress",
                rows: [["Completed", "136/200"], ["Remaining", "64 days"]],
                action: "View academic calendar",
              }} />
              <SmallCard card={{
                title: "Today&apos;s Schedule",
                rows: [["8:00 AM", "Faculty Devotion"], ["9:00 AM", "Chapel Service"], ["1:00 PM", "3rd Grade Field Trip"]],
                action: "View full calendar",
              }} />
              <SmallCard card={{
                title: "Top Attendance by Grade",
                rows: [["K", "97.8%"], ["1", "97.2%"], ["2", "96.8%"], ["9", "93.2%"]],
                action: "View attendance by class",
              }} />
            </section>
          </section>

          <RightRail />
        </main>
      </div>
    </div>
  );
}

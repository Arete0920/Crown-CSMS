import { Link } from "react-router";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { PATHS } from "../routes/paths.js";

// Avoid the historic sample-only dashboard when real care records are required.
export default function ExtendedCareDashboard() {
  return (
    <CrownLayout title="Extended Care" subtitle="Independent Before Care and After Care operations">
      <p>Select a program for source-backed daily statistics and care actions. Unavailable metrics are disclosed rather than inferred.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 16 }}>
        <section style={{ padding: 18, border: "1px solid var(--crown-border)", borderRadius: 8 }}>
          <h2>Before Care</h2>
          <p>Morning arrival, supervised attendance and authenticated school handoff.</p>
          <Link to={PATHS.BEFORECARE_DIRECTOR}>Open Before Care Director</Link>
        </section>
        <section style={{ padding: 18, border: "1px solid var(--crown-border)", borderRadius: 8 }}>
          <h2>After Care</h2>
          <p>Afternoon intake, current children in care and authorized checkout.</p>
          <Link to={PATHS.AFTERCARE_DIRECTOR}>Open After Care Director</Link>
        </section>
      </div>
      <p>Standalone sales, billing, staffing and hosted verification are separate acceptance gates.</p>
    </CrownLayout>
  );
}

import { useEffect, useMemo, useRef, useState } from "react";
import { getAdmissionsApplications } from "../api/admissions";
import { getSchoolId, getToken } from "../lib/api";
import { csvEscape, downloadTextFile } from "../lib/export/csv";
import Drawer from "../components/Drawer";

const STATUS_LABELS = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under review",
  NEEDS_INFO: "Needs info",
  ACCEPTED: "Accepted",
  WAITLISTED: "Waitlisted",
  DENIED: "Denied",
  WITHDRAWN: "Withdrawn",
};

export function AdmissionsPipelineList() {
  const token = getToken();
  const schoolId = getSchoolId();

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // sorting state
  const [rowSort, setRowSort] = useState({ key: "applicant", dir: "asc" });

  // detail drawer state
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);

    getAdmissionsApplications()
      .then((data) => {
        if (!alive) return;
        // Normalize once
        const normalized = (data || []).map((app) => ({
          id: app.id,
          applicant_name: app.applicant_name || "",
          student_first_name: app.student_first_name || "",
          student_last_name: app.student_last_name || "",
          status: app.status || "DRAFT",
          household_name: app.household_name || "",
          created_at: app.created_at || "",
          updated_at: app.updated_at || "",
        }));
        setApplications(normalized);
        setError(null);
      })
      .catch((err) => {
        if (!alive) return;
        console.error(err);
        setError({ message: err.message, status: err.status });
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  // sorted rows (client-side)
  const sortedRows = useMemo(() => {
    const arr = Array.isArray(applications) ? [...applications] : [];
    const dir = rowSort.dir === "asc" ? 1 : -1;

    arr.sort((a, b) => {
      if (rowSort.key === "applicant") {
        const na = (a.applicant_name || "").toLowerCase();
        const nb = (b.applicant_name || "").toLowerCase();
        if (na < nb) return -1 * dir;
        if (na > nb) return 1 * dir;
        return 0;
      }

      if (rowSort.key === "status") {
        const sa = a.status || "";
        const sb = b.status || "";
        if (sa < sb) return -1 * dir;
        if (sa > sb) return 1 * dir;
        return 0;
      }

      if (rowSort.key === "created_at") {
        const ta = new Date(a.created_at).getTime();
        const tb = new Date(b.created_at).getTime();
        return (ta - tb) * dir;
      }

      if (rowSort.key === "updated_at") {
        const ta = new Date(a.updated_at).getTime();
        const tb = new Date(b.updated_at).getTime();
        return (ta - tb) * dir;
      }

      return 0;
    });

    return arr;
  }, [applications, rowSort]);

  // CSV export
  const buildAdmissionsCsv = () => {
    const header = ["Applicant", "Status", "Household", "Submitted", "Updated"];
    const lines = [header.map(csvEscape).join(",")];

    for (const app of sortedRows) {
      const row = [
        app.applicant_name,
        STATUS_LABELS[app.status] || app.status,
        app.household_name,
        app.created_at ? new Date(app.created_at).toLocaleDateString() : "",
        app.updated_at ? new Date(app.updated_at).toLocaleDateString() : "",
      ];
      lines.push(row.map(csvEscape).join(","));
    }

    return lines.join("\n");
  };

  const onExportCsv = () => {
    const csv = buildAdmissionsCsv();
    const filename = `admissions_pipeline.csv`;
    downloadTextFile(filename, csv);
  };

  const isAuthed = !!token && !!schoolId;
  const hasApplications = applications.length > 0;

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h2>Admissions Pipeline</h2>

      {error && (
        <div style={{ margin: "12px 0", padding: 12, border: "1px solid #cc0000", background: "#ffe6e6" }}>
          <strong>Error:</strong> {error.message}
          {error.status && <div>Status: {error.status}</div>}
        </div>
      )}

      {loading && <div>Loading applications…</div>}

      {!loading && !hasApplications && (
        <div style={{ margin: "24px 0", padding: 16, borderLeft: "4px solid #ddd", background: "#f9f9f9" }}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: "1.1rem" }}>No applications yet</h3>
          <p>There are no applications to display.</p>
        </div>
      )}

      {!loading && hasApplications && (
        <>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              gap: 12,
              marginBottom: 10,
            }}
          >
            <button
              type="button"
              onClick={onExportCsv}
              style={{ padding: "6px 10px", fontSize: 13 }}
            >
              Export CSV ↓
            </button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", minWidth: 800 }}>
              <thead>
                <tr>
                  <th
                    style={{
                      position: "sticky",
                      left: 0,
                      top: 0,
                      background: "#fff",
                      zIndex: 11,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      textAlign: "left",
                      fontWeight: 600,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span>Applicant</span>
                      <button
                        type="button"
                        onClick={() =>
                          setRowSort((s) => ({
                            key: "applicant",
                            dir: s.key === "applicant" ? (s.dir === "asc" ? "desc" : "asc") : "asc",
                          }))
                        }
                        style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                      >
                        {rowSort.key === "applicant" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                      </button>
                    </div>
                  </th>

                  <th
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#fff",
                      zIndex: 10,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      textAlign: "left",
                      fontWeight: 600,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span>Status</span>
                      <button
                        type="button"
                        onClick={() =>
                          setRowSort((s) => ({
                            key: "status",
                            dir: s.key === "status" ? (s.dir === "asc" ? "desc" : "asc") : "asc",
                          }))
                        }
                        style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                      >
                        {rowSort.key === "status" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                      </button>
                    </div>
                  </th>

                  <th
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#fff",
                      zIndex: 10,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      textAlign: "left",
                      fontWeight: 600,
                    }}
                  >
                    Household
                  </th>

                  <th
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#fff",
                      zIndex: 10,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      textAlign: "left",
                      fontWeight: 600,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span>Submitted</span>
                      <button
                        type="button"
                        onClick={() =>
                          setRowSort((s) => ({
                            key: "created_at",
                            dir: s.key === "created_at" ? (s.dir === "asc" ? "desc" : "asc") : "desc",
                          }))
                        }
                        style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                      >
                        {rowSort.key === "created_at" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                      </button>
                    </div>
                  </th>

                  <th
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#fff",
                      zIndex: 10,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      textAlign: "left",
                      fontWeight: 600,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span>Updated</span>
                      <button
                        type="button"
                        onClick={() =>
                          setRowSort((s) => ({
                            key: "updated_at",
                            dir: s.key === "updated_at" ? (s.dir === "asc" ? "desc" : "asc") : "desc",
                          }))
                        }
                        style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                      >
                        {rowSort.key === "updated_at" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                      </button>
                    </div>
                  </th>
                </tr>
              </thead>

              <tbody>
                {sortedRows.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => setSelected(app)}
                    style={{ cursor: "pointer" }}
                  >
                    <td
                      style={{
                        position: "sticky",
                        left: 0,
                        background: "#fff",
                        zIndex: 1,
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      {app.applicant_name}
                    </td>

                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      {STATUS_LABELS[app.status] || app.status}
                    </td>

                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      {app.household_name}
                    </td>

                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      {app.created_at ? new Date(app.created_at).toLocaleDateString() : "—"}
                    </td>

                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      {app.updated_at ? new Date(app.updated_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? selected.applicant_name : ""}
      >
        {selected && (
          <div style={{ display: "grid", gap: 16 }}>
            {/* Application */}
            <section>
              <h4 style={{ marginBottom: 8 }}>Application</h4>
              <div><strong>Status:</strong> {STATUS_LABELS[selected.status] || selected.status}</div>
              <div><strong>Household:</strong> {selected.household_name}</div>
            </section>

            {/* Timeline */}
            <section>
              <h4 style={{ marginBottom: 8 }}>Timeline</h4>
              <div><strong>Submitted:</strong> {selected.created_at}</div>
              <div><strong>Updated:</strong> {selected.updated_at}</div>
            </section>

            {/* Identifiers */}
            <section style={{ fontSize: 12, color: "#666" }}>
              <details>
                <summary style={{ cursor: "pointer" }}>Identifiers</summary>
                <div style={{ marginTop: 6 }}>
                  <div><strong>Application ID:</strong> {selected.id}</div>
                </div>
              </details>
            </section>
          </div>
        )}
      </Drawer>
    </div>
  );
}

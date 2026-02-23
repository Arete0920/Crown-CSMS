import { useEffect, useState, useMemo } from "react";
import { getThreads, getThreadDetail } from "../api/communications";
import { csvEscape, downloadTextFile } from "../lib/export/csv";
import Drawer from "../components/Drawer";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";

export default function CommunicationsThreadsList() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [colSort, setColSort] = useState({ key: "last_message_at", dir: "desc" });
  const [selected, setSelected] = useState(null);
  const [threadDetail, setThreadDetail] = useState(null);
  const [loadingThread, setLoadingThread] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      try {
        setLoading(true);
        const threads = await getThreads();
        
        // Normalize: already comes in correct shape from API
        const normalized = threads.map((thread) => ({
          id: thread.thread_id,
          household_name: thread.household_name || "(No household)",
          student_name: thread.student_first_name && thread.student_last_name
            ? `${thread.student_first_name} ${thread.student_last_name}`
            : null,
          subject: thread.subject || "(No subject)",
          thread_type: thread.thread_type || "GENERAL",
          last_message_at: thread.last_message_at || null,
        }));

        if (mounted) {
          setData(normalized);
          setError(null);
        }
      } catch (err) {
        console.error("Failed to fetch threads:", err);
        if (mounted) {
          setError(err.message || "Failed to load threads");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  // Load thread detail when selected
  useEffect(() => {
    if (!selected) {
      setThreadDetail(null);
      return;
    }

    let mounted = true;

    async function fetchThread() {
      try {
        setLoadingThread(true);
        const detail = await getThreadDetail(selected.id);
        if (mounted) {
          setThreadDetail(detail);
        }
      } catch (err) {
        console.error("Failed to fetch thread detail:", err);
        if (mounted) {
          setThreadDetail({ messages: [], error: err.message });
        }
      } finally {
        if (mounted) {
          setLoadingThread(false);
        }
      }
    }

    fetchThread();
    return () => {
      mounted = false;
    };
  }, [selected]);

  // Sorting
  const sortedRows = useMemo(() => {
    if (!data.length) return [];

    const { key, dir } = colSort;
    const sorted = [...data];

    sorted.sort((a, b) => {
      let aVal = a[key];
      let bVal = b[key];

      // Dates
      if (key === "last_message_at") {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      }

      // Strings
      if (typeof aVal === "string") {
        aVal = aVal.toLowerCase();
        bVal = String(bVal || "").toLowerCase();
        return dir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      // Numeric or date comparison
      if (aVal < bVal) return dir === "asc" ? -1 : 1;
      if (aVal > bVal) return dir === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [data, colSort]);

  function handleSort(key) {
    setColSort((prev) => ({
      key,
      dir: prev.key === key && prev.dir === "asc" ? "desc" : "asc",
    }));
  }

  function handleExport() {
    if (!sortedRows.length) return;

    const headers = ["Household", "Student", "Subject", "Type", "Last Message"];
    const rows = [headers];

    sortedRows.forEach((thread) => {
      rows.push([
        csvEscape(thread.household_name),
        csvEscape(thread.student_name || ""),
        csvEscape(thread.subject),
        csvEscape(thread.thread_type),
        thread.last_message_at || "",
      ]);
    });

    const csvContent = rows.map((r) => r.join(",")).join("\n");
    downloadTextFile(csvContent, "threads.csv");
  }

  function formatDate(isoString) {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleString();
    } catch {
      return "";
    }
  }

  if (loading) {
    return (
      <CrownLayout title="Communications — Threads">
        <p>Loading...</p>
      </CrownLayout>
    );
  }

  if (error) {
    return (
      <CrownLayout title="Communications — Threads">
        <ErrorBanner title="Failed to load threads" message={error} />
      </CrownLayout>
    );
  }

  if (data.length === 0) {
    return (
      <CrownLayout title="Communications — Threads">
        <div style={{ marginTop: "1rem", color: "#6b7280" }}>
          No message threads yet
        </div>
      </CrownLayout>
    );
  }

  return (
    <CrownLayout title="Communications — Threads" subtitle="Director inbox">
      {/* Export bar */}
      <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
        <button
          className="crown-btn crown-btn-primary"
          onClick={handleExport}
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            borderCollapse: "collapse",
            width: "100%",
            fontSize: "0.875rem",
          }}
        >
          <thead>
            <tr style={{ background: "#f3f4f6" }}>
              <th
                onClick={() => handleSort("household_name")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid #e5e7eb",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "#f3f4f6",
                  zIndex: 10,
                }}
              >
                Household{" "}
                {colSort.key === "household_name" && (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("student_name")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid #e5e7eb",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "#f3f4f6",
                  zIndex: 10,
                }}
              >
                Student{" "}
                {colSort.key === "student_name" && (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("subject")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid #e5e7eb",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "#f3f4f6",
                  zIndex: 10,
                }}
              >
                Subject{" "}
                {colSort.key === "subject" && (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("thread_type")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid #e5e7eb",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "#f3f4f6",
                  zIndex: 10,
                }}
              >
                Type{" "}
                {colSort.key === "thread_type" && (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("last_message_at")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid #e5e7eb",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "#f3f4f6",
                  zIndex: 10,
                }}
              >
                Last Message{" "}
                {colSort.key === "last_message_at" && (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((thread) => (
              <tr
                key={thread.id}
                onClick={() => setSelected(thread)}
                style={{
                  cursor: "pointer",
                  borderBottom: "1px solid #e5e7eb",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#f9fafb";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "white";
                }}
              >
                <td style={{ padding: "0.75rem" }}>{thread.household_name}</td>
                <td style={{ padding: "0.75rem" }}>
                  {thread.student_name || "(None)"}
                </td>
                <td style={{ padding: "0.75rem" }}>{thread.subject}</td>
                <td style={{ padding: "0.75rem" }}>{thread.thread_type}</td>
                <td style={{ padding: "0.75rem" }}>
                  {thread.last_message_at ? formatDate(thread.last_message_at) : "(Never)"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Drawer */}
      {selected && (
        <Drawer onClose={() => setSelected(null)} width={520}>
          <div style={{ padding: "1.5rem" }}>
            <h2 style={{ marginTop: 0, marginBottom: "1.5rem", fontSize: "1.25rem" }}>
              Thread: {selected.subject}
            </h2>

            <div style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                Thread Info
              </h3>
              <div>
                <strong>Household:</strong> {selected.household_name}
              </div>
              {selected.student_name && (
                <div>
                  <strong>Student:</strong> {selected.student_name}
                </div>
              )}
              <div>
                <strong>Type:</strong> {selected.thread_type}
              </div>
              <div>
                <strong>Last Message:</strong>{" "}
                {selected.last_message_at ? formatDate(selected.last_message_at) : "(Never)"}
              </div>
            </div>

            {loadingThread && (
              <div style={{ color: "#6b7280" }}>Loading messages...</div>
            )}

            {!loadingThread && threadDetail && threadDetail.error && (
              <ErrorBanner title="Failed to load messages" message={threadDetail.error} />
            )}

            {!loadingThread && threadDetail && threadDetail.messages && (
              <div>
                <h3 style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                  Messages ({threadDetail.messages.length})
                </h3>
                <div
                  style={{
                    maxHeight: "400px",
                    overflowY: "auto",
                    border: "1px solid #e5e7eb",
                    borderRadius: "4px",
                  }}
                >
                  {threadDetail.messages.length === 0 && (
                    <div style={{ padding: "1rem", color: "#6b7280" }}>
                      No messages in this thread
                    </div>
                  )}
                  {threadDetail.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "1rem",
                        borderBottom: idx < threadDetail.messages.length - 1 ? "1px solid #f3f4f6" : "none",
                      }}
                    >
                      <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "0.25rem" }}>
                        {msg.sender_person
                          ? `${msg.sender_person.first_name} ${msg.sender_person.last_name}`
                          : "(Unknown sender)"}{" "}
                        · {formatDate(msg.sent_at)}
                      </div>
                      <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                        {msg.body}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <details style={{ fontSize: "0.875rem", marginTop: "1.5rem" }}>
              <summary style={{ cursor: "pointer", color: "#6b7280" }}>
                Identifiers
              </summary>
              <div style={{ marginTop: "0.5rem", fontFamily: "monospace", fontSize: "0.75rem" }}>
                <div>
                  <strong>Thread ID:</strong> {selected.id}
                </div>
              </div>
            </details>
          </div>
        </Drawer>
      )}
    </CrownLayout>
  );
}

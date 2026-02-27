/**
 * TableWidget — compact data table with column headers and rows.
 * Used for missing work, student lists, etc.
 */
import React from "react";

export default function TableWidget({ widget, onExpand }) {
  const { title, subtitle, data } = widget;
  const columns = data?.columns ?? [];
  const rows    = data?.rows ?? [];

  return (
    <div className="crown-card" style={{ height: "100%", overflowX: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div>
          <div style={{ fontWeight: 800 }}>{title}</div>
          {subtitle && <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 2 }}>{subtitle}</div>}
        </div>
        {onExpand && (
          <button
            onClick={onExpand}
            aria-label={`Expand ${title}`}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--crown-muted)", fontSize: 16, padding: 2 }}
          >
            ⤢
          </button>
        )}
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map((col, i) => (
              <th
                key={i}
                style={{
                  textAlign: "left",
                  padding: "4px 8px",
                  borderBottom: "1px solid var(--crown-border)",
                  color: "var(--crown-muted)",
                  fontWeight: 700,
                  fontSize: 11,
                  textTransform: "uppercase",
                  letterSpacing: 0.4,
                  whiteSpace: "nowrap",
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length || 1}
                style={{ padding: "12px 8px", color: "var(--crown-muted)", fontStyle: "italic", textAlign: "center" }}
              >
                No items
              </td>
            </tr>
          ) : (
            rows.map((row, ri) => (
              <tr key={ri} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                {row.map((cell, ci) => (
                  <td key={ci} style={{ padding: "6px 8px" }}>
                    {typeof cell === "number" ? (
                      <span
                        style={{
                          background: "rgba(255,93,93,0.15)",
                          color: "var(--crown-danger)",
                          borderRadius: 6,
                          padding: "2px 7px",
                          fontWeight: 700,
                          fontSize: 12,
                        }}
                      >
                        {cell}
                      </span>
                    ) : (
                      cell
                    )}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

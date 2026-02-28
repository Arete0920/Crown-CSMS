import { useEffect, useMemo, useState } from "react";

/**
 * Safe read-only data loader for the Board Executive Dashboard.
 * Attempts live endpoints; falls back to demo data on any failure.
 * Replace the URL constants with real board endpoints when available.
 */

const URLS = {
  kpis:    "/api/v1/board/kpis/",
  trends:  "/api/v1/board/trends/",
  risk:    "/api/v1/board/risk/",
  drivers: "/api/v1/board/drivers/",
};

const DEMO = {
  kpis: {
    enrollment:    312,
    netTuition:    2_850_000,
    aidAwarded:    640_000,
    attendancePct: 94.6,
  },
  trends: {
    enrollment: [
      { label: "Sep", value: 298 },
      { label: "Oct", value: 301 },
      { label: "Nov", value: 306 },
      { label: "Dec", value: 309 },
      { label: "Jan", value: 312 },
    ],
    netTuition: [
      { label: "Sep", value: 520_000 },
      { label: "Oct", value: 555_000 },
      { label: "Nov", value: 575_000 },
      { label: "Dec", value: 590_000 },
      { label: "Jan", value: 610_000 },
    ],
  },
  risk: [
    { area: "Enrollment", status: "Stable", note: "Re-enrollment trending +2.1% YoY" },
    { area: "Cash Flow",  status: "Watch",  note: "2 accounts >30 days past due" },
    { area: "Staffing",   status: "Stable", note: "No critical vacancies" },
    { area: "Culture",    status: "Stable", note: "Parent sentiment steady" },
  ],
  topDrivers: [
    { metric: "Re-enrollment", value: "91.4%", note: "Above target" },
    { metric: "Aid Yield",     value: "78%",   note: "Target range" },
    { metric: "Attendance",    value: "94.6%", note: "Seasonal dip normal" },
    { metric: "Discipline",    value: "Low",   note: "Incidents down 8%" },
  ],
};

async function safeJson(res) {
  const text = await res.text();
  try { return JSON.parse(text); } catch { return null; }
}

/**
 * @param {{ token: string, schoolId: string }} auth
 * @returns {{ data: typeof DEMO, loading: boolean, live: boolean, error: string }}
 */
export function useBoardExecutiveData({ token, schoolId }) {
  const [data,    setData]    = useState(DEMO);
  const [loading, setLoading] = useState(true);
  const [live,    setLive]    = useState(false);
  const [error,   setError]   = useState("");

  const headers = useMemo(() => {
    const h = { Accept: "application/json" };
    if (token)    h["Authorization"] = `Bearer ${token}`;
    if (schoolId) h["X-School-Id"]   = String(schoolId);
    return h;
  }, [token, schoolId]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const [rk, rt, rr, rd] = await Promise.allSettled([
          fetch(URLS.kpis,    { headers }),
          fetch(URLS.trends,  { headers }),
          fetch(URLS.risk,    { headers }),
          fetch(URLS.drivers, { headers }),
        ]);

        const next = structuredClone(DEMO);
        let anyLive = false;

        if (rk.status === "fulfilled" && rk.value.ok) {
          const j = await safeJson(rk.value); if (j) { next.kpis      = j; anyLive = true; }
        }
        if (rt.status === "fulfilled" && rt.value.ok) {
          const j = await safeJson(rt.value); if (j) { next.trends     = j; anyLive = true; }
        }
        if (rr.status === "fulfilled" && rr.value.ok) {
          const j = await safeJson(rr.value); if (j) { next.risk       = j; anyLive = true; }
        }
        if (rd.status === "fulfilled" && rd.value.ok) {
          const j = await safeJson(rd.value); if (j) { next.topDrivers = j; anyLive = true; }
        }

        if (!cancelled) { setData(next); setLive(anyLive); }
      } catch (e) {
        if (!cancelled) setError(e?.message || "Failed to load board data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [headers]);

  return { data, loading, live, error };
}

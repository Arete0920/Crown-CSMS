import { useEffect, useState } from "react";
import { authenticatedJson } from "../utils/authClient.js";

/**
 * Read-only data loader for the Board Executive Dashboard.
 *
 * Protected first-party requests must use the canonical authenticated transport.
 * The board aggregate is marked live only when every required source succeeds;
 * partial live responses are never overlaid onto demo data and represented as
 * a live aggregate.
 */

const URLS = {
  kpis: "/api/v1/board/kpis/",
  trends: "/api/v1/board/trends/",
  risk: "/api/v1/board/risk/",
  drivers: "/api/v1/board/drivers/",
};

const DEMO = {
  kpis: {
    enrollment: 312,
    netTuition: 2_850_000,
    aidAwarded: 640_000,
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
    { area: "Cash Flow", status: "Watch", note: "2 accounts >30 days past due" },
    { area: "Staffing", status: "Stable", note: "No critical vacancies" },
    { area: "Culture", status: "Stable", note: "Parent sentiment steady" },
  ],
  topDrivers: [
    { metric: "Re-enrollment", value: "91.4%", note: "Above target" },
    { metric: "Aid Yield", value: "78%", note: "Target range" },
    { metric: "Attendance", value: "94.6%", note: "Seasonal dip normal" },
    { metric: "Discipline", value: "Low", note: "Incidents down 8%" },
  ],
};

/**
 * Authentication and selected-school context are owned by authClient.js.
 *
 * @returns {{ data: typeof DEMO, loading: boolean, live: boolean, error: string }}
 */
export function useBoardExecutiveData() {
  const [data, setData] = useState(DEMO);
  const [loading, setLoading] = useState(true);
  const [live, setLive] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      setLive(false);

      try {
        const [kpis, trends, risk, topDrivers] = await Promise.all([
          authenticatedJson(URLS.kpis),
          authenticatedJson(URLS.trends),
          authenticatedJson(URLS.risk),
          authenticatedJson(URLS.drivers),
        ]);

        if (!cancelled) {
          setData({ kpis, trends, risk, topDrivers });
          setLive(true);
        }
      } catch (cause) {
        console.error("[Dashboard Integration] Board Executive data fetch failed — using DEMO data", {
          endpoints: URLS,
          error: cause?.message || cause,
          timestamp: new Date().toISOString(),
        });
        if (!cancelled) {
          setData(DEMO);
          setLive(false);
          setError(cause?.message || "Failed to load complete live board data.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, live, error };
}

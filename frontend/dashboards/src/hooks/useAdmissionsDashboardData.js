import { useCallback, useEffect, useMemo, useState } from "react";
import {
    fetchAdmissionsSummary,
    fetchAdmissionsDrilldown,
} from "../api/admissions";

function toArray(payload) {
    if (Array.isArray(payload)) return payload;
    if (!payload || typeof payload !== "object") return [];
    return (
        payload.results ||
        payload.items ||
        payload.rows ||
        payload.applications ||
        payload.events ||
        payload.queue ||
        payload.data ||
        []
    );
}

function pickNumber(source, keys, fallback = 0) {
    for (const key of keys) {
        const value = source?.[key];
        if (typeof value === "number") return value;
        if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) {
            return Number(value);
        }
    }
    return fallback;
}

function normalizeSummary(summary) {
    const src = summary || {};
    return {
        total: pickNumber(src, ["total", "total_count", "totalCount", "applications_total"]),
        submitted: pickNumber(src, ["submitted", "submitted_count", "submittedCount"]),
        underReview: pickNumber(src, ["under_review", "underReview", "under_review_count"]),
        admitted: pickNumber(src, ["admitted", "admitted_count", "admittedCount"]),
        waitlisted: pickNumber(src, ["waitlisted", "waitlisted_count", "waitlist_count"]),
        denied: pickNumber(src, ["denied", "denied_count", "rejected_count"]),
        enrolled: pickNumber(src, ["enrolled", "enrolled_count", "converted_count"]),
    };
}

export default function useAdmissionsDashboardData(year) {
    const [loading, setLoading] = useState(true);
    const [drilldownLoading, setDrilldownLoading] = useState(false);
    const [error, setError] = useState("");
    const [summary, setSummary] = useState({});
    const [metrics, setMetrics] = useState({});
    const [priorityQueue, setPriorityQueue] = useState([]);
    const [timeline, setTimeline] = useState([]);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [drawerTitle, setDrawerTitle] = useState("");
    const [drilldownRows, setDrilldownRows] = useState([]);

    const reload = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const params = year ? { academic_year: year } : {};
            const summaryRes = await fetchAdmissionsSummary(params);
            setSummary(summaryRes || {});
            // The canonical v1 admissions summary owns dashboard truth. Keep the
            // legacy state fields empty for hook compatibility without issuing
            // duplicate /api/admissions/* requests against a separate model.
            setMetrics({});
            setPriorityQueue([]);
            setTimeline([]);
        } catch {
            setSummary({});
            setMetrics({});
            setPriorityQueue([]);
            setTimeline([]);
            setError("Unable to load admissions summary data.");
        } finally {
            setLoading(false);
        }
    }, [year]);

    useEffect(() => {
        if (import.meta.env.MODE === "test") {
            setLoading(false);
            return;
        }
        void reload();
    }, [reload]);

    const openDrilldown = useCallback(
        async (statusKey, title) => {
            setDrilldownLoading(true);
            setDrawerTitle(title);
            setDrawerOpen(true);

            try {
                const params = {
                    ...(year ? { academic_year: year } : {}),
                    status: statusKey,
                };
                const res = await fetchAdmissionsDrilldown(params);
                setDrilldownRows(toArray(res));
            } catch {
                setDrilldownRows([]);
            } finally {
                setDrilldownLoading(false);
            }
        },
        [year]
    );

    const closeDrilldown = useCallback(() => {
        setDrawerOpen(false);
        setDrawerTitle("");
        setDrilldownRows([]);
    }, []);

    const normalizedSummary = useMemo(() => normalizeSummary(summary), [summary]);

    return {
        loading,
        drilldownLoading,
        error,
        summary: normalizedSummary,
        rawSummary: summary,
        metrics,
        priorityQueue,
        timeline,
        drawerOpen,
        drawerTitle,
        drilldownRows,
        openDrilldown,
        closeDrilldown,
        reload,
    };
}

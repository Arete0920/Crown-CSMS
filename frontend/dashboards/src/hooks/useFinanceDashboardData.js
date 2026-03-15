import { useCallback, useEffect, useState } from "react";
import {
    fetchFinanceMetrics,
    fetchFinanceSummary,
    fetchInvoices,
} from "../api/finance";

function toRows(payload) {
    if (Array.isArray(payload)) return payload;
    if (!payload || typeof payload !== "object") return [];
    return payload.results || payload.items || payload.rows || [];
}

export default function useFinanceDashboardData() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [metrics, setMetrics] = useState(null);
    const [summary, setSummary] = useState(null);
    const [invoices, setInvoices] = useState([]);

    const reload = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const [metricsRes, summaryRes, invoicesRes] = await Promise.all([
                fetchFinanceMetrics(),
                fetchFinanceSummary(),
                fetchInvoices(),
            ]);

            setMetrics(metricsRes || {});
            setSummary(summaryRes || {});
            setInvoices(toRows(invoicesRes));
        } catch (err) {
            setError(err?.message || "Unable to load finance dashboard data.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void reload();
    }, [reload]);

    return {
        loading,
        error,
        metrics,
        summary,
        invoices,
        reload,
    };
}

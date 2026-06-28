/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "../lib/api";

/**
 * Stage 2 — Finance KPI Widget
 *
 * Displays reconciliation match status, revenue summary, and open chargebacks.
 * Fetches from:
 *   GET /api/v1/finance/kpis/
 *   GET /api/v1/finance/chargebacks/
 *
 * Props:
 *   schoolId  (string)  — required, passed as X-School-Id header via apiFetch
 *   className (string)  — optional additional CSS classes
 */
export default function FinanceKPI({ schoolId, className = "" }) {
  const [kpis, setKpis] = useState(null);
  const [chargebacks, setChargebacks] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiData, cbData] = await Promise.all([
        apiFetch("/api/v1/finance/kpis/", { schoolId }),
        apiFetch("/api/v1/finance/chargebacks/", { schoolId }),
      ]);
      setKpis(kpiData);
      setChargebacks(cbData);
    } catch (err) {
      setError(err?.message ?? "Failed to load finance data");
    } finally {
      setLoading(false);
    }
  }, [schoolId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className={`finance-kpi-card ${className}`} aria-busy="true">
        <p>Loading finance data…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`finance-kpi-card finance-kpi-card--error ${className}`} role="alert">
        <p>Finance data unavailable: {error}</p>
      </div>
    );
  }

  const recon = kpis?.reconciliation ?? {};
  const reconMatch = recon.match === true;

  return (
    <section
      className={`finance-kpi-card ${className}`}
      aria-label="Finance KPI Summary"
    >
      <h2 className="finance-kpi-card__title">Finance Summary</h2>

      <dl className="finance-kpi-card__grid">
        {/* Revenue */}
        <div className="finance-kpi-card__stat">
          <dt>Total Revenue</dt>
          <dd aria-label={`$${kpis?.total_successful_payments?.toLocaleString()}`}>
            ${kpis?.total_successful_payments?.toLocaleString("en-US", {
              minimumFractionDigits: 2,
            })}
          </dd>
        </div>

        {/* Net Revenue */}
        <div className="finance-kpi-card__stat">
          <dt>Net Revenue</dt>
          <dd>
            ${kpis?.net_revenue?.toLocaleString("en-US", {
              minimumFractionDigits: 2,
            })}
          </dd>
        </div>

        {/* Reconciliation */}
        <div className="finance-kpi-card__stat">
          <dt>Processor Reconciliation</dt>
          <dd
            className={reconMatch ? "kpi--ok" : "kpi--warn"}
            aria-label={reconMatch ? "Balanced" : `Variance: $${recon.difference}`}
          >
            {reconMatch ? (
              "✓ Balanced"
            ) : (
              <span>
                ⚠ Variance: ${Math.abs(recon.difference ?? 0).toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                })}
              </span>
            )}
          </dd>
        </div>

        {/* Open Chargebacks */}
        <div className="finance-kpi-card__stat">
          <dt>Open Disputes</dt>
          <dd
            className={chargebacks?.open_cases > 0 ? "kpi--warn" : "kpi--ok"}
            aria-label={`${chargebacks?.open_cases ?? 0} open chargebacks`}
          >
            {chargebacks?.open_cases ?? 0}
            {chargebacks?.open_cases > 0 && (
              <span className="kpi--subtext">
                {" "}(${chargebacks?.open_disputed_amount?.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                })})
              </span>
            )}
          </dd>
        </div>
      </dl>

      <button
        type="button"
        className="finance-kpi-card__refresh"
        onClick={load}
        aria-label="Refresh finance data"
      >
        Refresh
      </button>
    </section>
  );
}


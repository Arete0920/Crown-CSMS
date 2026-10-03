import { useCallback, useEffect, useState } from "react";
import { authenticatedJson } from "../../utils/authClient";
import { getCurrentUserRoles } from "../../auth/roleAdapter";

const sandboxEnabled = String(import.meta.env.VITE_SANDBOX_MODE || "") === "1";

function dollars(cents) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(cents || 0) / 100);
}

export default function SandboxFinanceTransactionPanel() {
  const eligible = getCurrentUserRoles().includes("finance_director");
  const [state, setState] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!sandboxEnabled || !eligible) return;
    setError("");
    try {
      setState(await authenticatedJson("/api/v1/sandbox/finance/state/"));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load finance transaction state.");
    }
  }, [eligible]);

  useEffect(() => { void load(); }, [load]);
  if (!sandboxEnabled || !eligible) return null;

  async function applyPayment() {
    setSaving(true);
    setError("");
    try {
      const next = await authenticatedJson("/api/v1/sandbox/finance/apply-payment/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setState(next);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to apply demo payment.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section data-testid="sandbox-finance-transaction" className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Finance Transaction Proof</h2>
          <p className="mt-1 text-sm text-slate-600">
            Work the seeded Reed family account: review authoritative balance/history, apply a protected manual demo payment, reconcile it to the ledger, and verify void and over-refund controls.
          </p>
        </div>
        <button type="button" onClick={applyPayment} disabled={saving || state?.reconciliation_status === "reconciled"} className="inline-flex items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {saving ? "Applying..." : state?.reconciliation_status === "reconciled" ? "Payment Reconciled" : "Apply Demo Payment"}
        </button>
      </div>

      {error ? <div role="alert" className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      {state ? (
        <dl className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-slate-500">Family account</dt><dd data-testid="finance-family-account" className="font-medium text-slate-900">{state.family_account}</dd></div>
          <div><dt className="text-slate-500">Authoritative balance</dt><dd data-testid="finance-authoritative-balance" className="font-medium text-slate-900">{dollars(state.authoritative_balance_cents)}</dd></div>
          <div><dt className="text-slate-500">Target obligation</dt><dd className="font-medium text-slate-900">{state.obligation_reference}</dd></div>
          <div><dt className="text-slate-500">Target remaining</dt><dd data-testid="finance-remaining" className="font-medium text-slate-900">{dollars(state.remaining_cents)}</dd></div>
          <div><dt className="text-slate-500">Payment history</dt><dd data-testid="finance-payment-history" className="font-medium text-slate-900">{state.payment_history_count}</dd></div>
          <div><dt className="text-slate-500">Allocation history</dt><dd data-testid="finance-allocation-history" className="font-medium text-slate-900">{state.allocation_history_count}</dd></div>
          <div><dt className="text-slate-500">Voided charges excluded</dt><dd data-testid="finance-void-integrity" className="font-medium text-slate-900">{state.voided_obligation_count} · {dollars(state.voided_amount_excluded_cents)}</dd></div>
          <div><dt className="text-slate-500">Reconciliation</dt><dd data-testid="finance-reconciliation" className="font-medium text-slate-900">{state.reconciliation_status}</dd></div>
          <div><dt className="text-slate-500">Exception control</dt><dd data-testid="finance-exception-control" className="font-medium text-slate-900">{state.exception_control_status}</dd></div>
        </dl>
      ) : null}

      {state?.over_refund_blocked ? (
        <p className="mt-3 text-sm font-medium text-emerald-700">Over-refund blocked; voided charges excluded; settlement reconciled. No external payment processed.</p>
      ) : null}
    </section>
  );
}

import useFinanceDashboardData from "../hooks/useFinanceDashboardData";
import CrownLayout from "../components/crown/CrownLayout.jsx";

function metricValue(source, key, fallback = "—") {
  const value = source?.[key];
  return value === undefined || value === null || value === ""
    ? fallback
    : value;
}

function InvoiceList({ invoices }) {
  const openOnly = invoices.filter((row) => Number(row.balance_due || 0) > 0);

  if (!openOnly.length) {
    return <p className="text-sm text-slate-600">No open invoices found.</p>;
  }

  return (
    <ul className="space-y-2 text-sm text-slate-700">
      {openOnly.slice(0, 10).map((row) => (
        <li key={row.id} className="rounded border border-slate-200 px-3 py-2">
          <div className="font-medium text-slate-900">
            {row.invoice_number || `Invoice ${row.id}`}
          </div>
          <div className="text-slate-600">
            {`${row.household_name || "Household"} • Due ${row.balance_due}`}
          </div>
        </li>
      ))}
    </ul>
  );
}

function KpiCard({ title, value, subtitle }) {
  return (
    <article className="h-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
      {subtitle ? <p className="mt-2 text-sm text-slate-600">{subtitle}</p> : null}
    </article>
  );
}

export default function FinanceDashboard() {
  const { loading, error, metrics, summary, invoices, reload } =
    useFinanceDashboardData();

  return (
    <CrownLayout
      title="Finance"
      subtitle="Live finance metrics and invoice visibility"
    >
      <section className="space-y-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Finance Dashboard</h1>
            <p className="text-sm text-slate-600">Live finance metrics and invoice visibility.</p>
          </div>

          <button
            type="button"
            onClick={reload}
            className="inline-flex items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </header>

        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="py-8 text-center text-sm text-slate-600">Loading finance data...</div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div>
                <KpiCard
                  title="AR Outstanding"
                  value={metricValue(metrics, "ar_outstanding")}
                />
              </div>
              <div>
                <KpiCard
                  title="Open Invoices"
                  value={metricValue(metrics, "open_invoices")}
                />
              </div>
              <div>
                <KpiCard
                  title="Collected This Month"
                  value={metricValue(metrics, "collected_month")}
                />
              </div>
              <div>
                <KpiCard
                  title="Payment Failures"
                  value={metricValue(metrics, "payment_failures")}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Finance Summary</h2>
                <hr className="my-3 border-slate-200" />
                      {!summary ? (
                        <p className="text-sm text-slate-600">No summary data available.</p>
                      ) : (
                        <div className="space-y-2">
                          {Object.entries(summary).map(([key, value]) => (
                            <div
                              key={key}
                              className="flex items-center justify-between gap-2 text-sm"
                            >
                              <span className="text-slate-600">
                                {key}
                              </span>
                              <span className="font-medium text-slate-900">
                                {String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Open Invoices</h2>
                <hr className="my-3 border-slate-200" />
                      <InvoiceList invoices={invoices} />
              </section>
            </div>
          </>
        )}
      </section>
    </CrownLayout>
  );
}

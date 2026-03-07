/**
 * EnrollmentPaymentPlanSection.jsx
 * =================================
 * Read-only aid-aware payment plan preview for the enrollment UI.
 * No @mui — native HTML + inline styles only.
 *
 * Props:
 *   tuitionCents     number   gross annual tuition in cents
 *   aidCents         number   total aid awarded in cents
 *   paymentPlans     object   PaymentPlanPolicy from finance snapshot
 */

const PLAN_LABELS = {
  allow_pay_in_full: "Pay in full",
  allow_semi_annual: "Semi-annual (2 payments)",
  allow_quarterly: "Quarterly (4 payments)",
  allow_10_month: "10-month plan",
  allow_12_month: "12-month plan",
};

const PLAN_MONTHS = {
  allow_pay_in_full: 1,
  allow_semi_annual: 2,
  allow_quarterly: 4,
  allow_10_month: 10,
  allow_12_month: 12,
};

function fmt(cents) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    (cents ?? 0) / 100
  );
}

export default function EnrollmentPaymentPlanSection({
  tuitionCents = 0,
  aidCents = 0,
  paymentPlans = {},
}) {
  const netCents = Math.max(0, tuitionCents - aidCents);

  const activePlans = Object.entries(PLAN_LABELS)
    .filter(([key]) => paymentPlans[key])
    .map(([key, label]) => {
      const installments = PLAN_MONTHS[key];
      const perInstallment = installments === 1 ? netCents : Math.ceil(netCents / installments);

      let discountNote = null;
      if (key === "allow_pay_in_full" && (paymentPlans.pay_in_full_discount_percent_bp ?? 0) > 0) {
        const discountBp = paymentPlans.pay_in_full_discount_percent_bp;
        const discountCents = Math.round((netCents * discountBp) / 10000);
        discountNote = `Includes ${discountBp / 100}% early-pay discount (saves ${fmt(discountCents)})`;
      }

      return { key, label, installments, perInstallment, discountNote };
    });

  const hasLateFee = (paymentPlans.late_fee_flat_cents ?? 0) > 0;
  const achNote = paymentPlans.ach_required_for_installments
    ? "ACH (bank transfer) required for installment plans."
    : null;

  return (
    <div
      style={{
        background: "var(--crown-surface)",
        border: "1px solid var(--crown-border)",
        borderRadius: 8,
        padding: 20,
        maxWidth: 600,
      }}
    >
      <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4, color: "var(--crown-ink)" }}>
        Payment Plan Options
      </h3>

      <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 16 }}>
        <span>Gross tuition: {fmt(tuitionCents)}</span>
        {aidCents > 0 && (
          <>
            &nbsp;·&nbsp;
            <span style={{ color: "var(--crown-ok)" }}>Aid: −{fmt(aidCents)}</span>
            &nbsp;·&nbsp;
            <span style={{ fontWeight: 600, color: "var(--crown-ink)" }}>Net: {fmt(netCents)}</span>
          </>
        )}
      </div>

      {activePlans.length === 0 && (
        <p style={{ fontSize: 13, color: "var(--crown-muted)" }}>No payment plans configured.</p>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--crown-border)" }}>
            <th style={{ textAlign: "left", paddingBottom: 8, color: "var(--crown-muted)", fontWeight: 500 }}>
              Plan
            </th>
            <th style={{ textAlign: "right", paddingBottom: 8, color: "var(--crown-muted)", fontWeight: 500 }}>
              Installments
            </th>
            <th style={{ textAlign: "right", paddingBottom: 8, color: "var(--crown-muted)", fontWeight: 500 }}>
              Each
            </th>
          </tr>
        </thead>
        <tbody>
          {activePlans.map(({ key, label, installments, perInstallment, discountNote }) => (
            <tr
              key={key}
              style={{ borderBottom: "1px solid var(--crown-border)" }}
            >
              <td style={{ padding: "8px 0", verticalAlign: "top" }}>
                <div>{label}</div>
                {discountNote && (
                  <div style={{ fontSize: 11, color: "var(--crown-ok)", marginTop: 2 }}>{discountNote}</div>
                )}
              </td>
              <td style={{ textAlign: "right", padding: "8px 0", verticalAlign: "top" }}>
                {installments}
              </td>
              <td style={{ textAlign: "right", padding: "8px 0", verticalAlign: "top", fontWeight: 600 }}>
                {fmt(perInstallment)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {(achNote || hasLateFee) && (
        <div
          style={{
            marginTop: 14,
            padding: "10px 12px",
            background: "var(--crown-surface-2)",
            borderRadius: 6,
            fontSize: 12,
            color: "var(--crown-muted)",
          }}
        >
          {achNote && <div>ℹ {achNote}</div>}
          {hasLateFee && (
            <div style={{ marginTop: achNote ? 4 : 0 }}>
              ⚠ Late fee: {fmt(paymentPlans.late_fee_flat_cents)} after{" "}
              {paymentPlans.late_fee_grace_days} grace day(s).
            </div>
          )}
        </div>
      )}
    </div>
  );
}

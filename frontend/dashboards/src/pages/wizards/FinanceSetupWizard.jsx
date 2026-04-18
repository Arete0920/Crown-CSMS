/**
 * FinanceSetupWizard.jsx
 * ======================
 * Year-locked financial canon wizard: Tuition ? Discounts ? Aid ? Plans ? Extended Care ? Review.
 * Crown component library only — no @mui/material.
 */

import { useEffect, useState } from "react";
import { fetchFinanceStatus, lockFinancePolicy, saveFinancePolicy } from "../../api/financeSetupApi.js";

// -- Layout primitives ---------------------------------------------------------

function WizardShell({ title, children }) {
  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "32px 20px", fontFamily: "inherit" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>{title}</h1>
      {children}
    </div>
  );
}

function StepCard({ label, children }) {
  return (
    <div
      style={{
        background: "var(--crown-surface)",
        border: "1px solid var(--crown-border)",
        borderRadius: 8,
        padding: 24,
        marginBottom: 24,
      }}
    >
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--crown-ink)" }}>{label}</h2>
      {children}
    </div>
  );
}

function FieldRow({ label, hint, children }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 12, marginBottom: 14, alignItems: "start" }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--crown-ink)" }}>{label}</div>
        {hint && <div style={{ fontSize: 11, color: "var(--crown-muted)", marginTop: 2 }}>{hint}</div>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function Toggle({ value, onChange, disabled }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: disabled ? "default" : "pointer" }}>
      <input
        type="checkbox"
        checked={!!value}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        disabled={disabled}
        style={{ width: 16, height: 16 }}
      />
      <span style={{ fontSize: 13, color: disabled ? "var(--crown-muted)" : "var(--crown-ink)" }}>
        {value ? "Enabled" : "Disabled"}
      </span>
    </label>
  );
}

function NumInput({ value, onChange, disabled, min = 0, step = 1 }) {
  return (
    <input
      type="number"
      value={value ?? ""}
      min={min}
      step={step}
      onChange={(e) => !disabled && onChange(Number(e.target.value))}
      disabled={disabled}
      style={{
        width: 140,
        padding: "6px 10px",
        border: "1px solid var(--crown-border)",
        borderRadius: 6,
        fontSize: 13,
        background: disabled ? "var(--crown-surface-2)" : "var(--crown-surface)",
      }}
    />
  );
}

function Select({ value, onChange, options, disabled }) {
  return (
    <select
      value={value}
      onChange={(e) => !disabled && onChange(e.target.value)}
      disabled={disabled}
      style={{
        padding: "6px 10px",
        border: "1px solid var(--crown-border)",
        borderRadius: 6,
        fontSize: 13,
        background: disabled ? "var(--crown-surface-2)" : "var(--crown-surface)",
      }}
    >
      {options.map(({ value: v, label }) => (
        <option key={v} value={v}>
          {label}
        </option>
      ))}
    </select>
  );
}

/** Display cents as dollars label (read aid) */
function MoneyCentsInput({ value, onChange, disabled }) {
  const dollars = ((value ?? 0) / 100).toFixed(2);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ fontSize: 13, color: "var(--crown-muted)" }}>$</span>
      <input
        type="number"
        value={dollars}
        min={0}
        step={0.01}
        onChange={(e) => !disabled && onChange(Math.round(parseFloat(e.target.value || "0") * 100))}
        disabled={disabled}
        style={{
          width: 140,
          padding: "6px 10px",
          border: "1px solid var(--crown-border)",
          borderRadius: 6,
          fontSize: 13,
          background: disabled ? "var(--crown-surface-2)" : "var(--crown-surface)",
        }}
      />
    </div>
  );
}

// -- Default wizardState shape -------------------------------------------------

function defaults() {
  return {
    tuition: {
      tuition_mode: "grade_based",
      currency: "USD",
      flat_annual_tuition_cents: 0,
      fees_apply_to_aid: false,
      fees_apply_to_discounts: false,
    },
    discounts: {
      discounts_apply_to: "tuition_only",
      stacking_enabled: true,
      sibling_discount_enabled: true,
      sibling_discount_percent_bp: 1000,
      sibling_discount_applies_from_child: 2,
      staff_discount_enabled: true,
      staff_discount_percent_bp: 0,
      ministry_discount_enabled: false,
      ministry_discount_percent_bp: 0,
      max_discount_percent_bp: 10000,
    },
    aid: {
      application_fee_cents: 5500,
      aid_applies_to: "tuition_only",
      distribute_aid_evenly: true,
      max_aid_per_student_cents: 0,
      max_aid_per_family_cents: 0,
    },
    payment_plans: {
      allow_pay_in_full: true,
      allow_semi_annual: true,
      allow_quarterly: true,
      allow_10_month: true,
      allow_12_month: true,
      ach_required_for_installments: true,
      pay_in_full_discount_percent_bp: 0,
      late_fee_grace_days: 5,
      late_fee_flat_cents: 0,
    },
    extended_care: {
      supports_annual: false,
      supports_monthly: true,
      supports_weekly: false,
      supports_drop_in_daily: true,
      supports_hybrid: true,
      late_pickup_grace_minutes: 5,
      late_pickup_fee_cents: 0,
      late_pickup_per_minute_cents: 0,
      post_to_ledger: true,
      include_in_tuition_plan: false,
    },
  };
}

// -- Step renderers ------------------------------------------------------------

function StepTuition({ data, onChange, locked }) {
  const set = (k) => (v) => onChange({ ...data, [k]: v });
  return (
    <StepCard label="Step 1 — Tuition Structure">
      <FieldRow label="Tuition Mode">
        <Select
          value={data.tuition_mode}
          onChange={set("tuition_mode")}
          disabled={locked}
          options={[
            { value: "grade_based", label: "Grade-based rates" },
            { value: "flat", label: "Flat annual amount" },
          ]}
        />
      </FieldRow>
      <FieldRow label="Currency">
        <Select
          value={data.currency}
          onChange={set("currency")}
          disabled={locked}
          options={[
            { value: "USD", label: "USD" },
            { value: "CAD", label: "CAD" },
          ]}
        />
      </FieldRow>
      <FieldRow label="Flat Annual Tuition" hint="Used when mode is 'flat'">
        <MoneyCentsInput value={data.flat_annual_tuition_cents} onChange={set("flat_annual_tuition_cents")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Fees apply to Aid">
        <Toggle value={data.fees_apply_to_aid} onChange={set("fees_apply_to_aid")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Fees apply to Discounts">
        <Toggle value={data.fees_apply_to_discounts} onChange={set("fees_apply_to_discounts")} disabled={locked} />
      </FieldRow>
    </StepCard>
  );
}

function StepDiscounts({ data, onChange, locked }) {
  const set = (k) => (v) => onChange({ ...data, [k]: v });
  return (
    <StepCard label="Step 2 — Discount Policy">
      <FieldRow label="Discounts apply to">
        <Select
          value={data.discounts_apply_to}
          onChange={set("discounts_apply_to")}
          disabled={locked}
          options={[
            { value: "tuition_only", label: "Tuition only" },
            { value: "tuition_and_fees", label: "Tuition + Fees" },
          ]}
        />
      </FieldRow>
      <FieldRow label="Discount stacking">
        <Toggle value={data.stacking_enabled} onChange={set("stacking_enabled")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Sibling discount">
        <Toggle value={data.sibling_discount_enabled} onChange={set("sibling_discount_enabled")} disabled={locked} />
      </FieldRow>
      {data.sibling_discount_enabled && (
        <>
          <FieldRow label="Sibling discount (basis pts)" hint="1000 bp = 10%">
            <NumInput value={data.sibling_discount_percent_bp} onChange={set("sibling_discount_percent_bp")} disabled={locked} />
          </FieldRow>
          <FieldRow label="Applies from child #">
            <NumInput value={data.sibling_discount_applies_from_child} onChange={set("sibling_discount_applies_from_child")} disabled={locked} min={1} />
          </FieldRow>
        </>
      )}
      <FieldRow label="Staff discount">
        <Toggle value={data.staff_discount_enabled} onChange={set("staff_discount_enabled")} disabled={locked} />
      </FieldRow>
      {data.staff_discount_enabled && (
        <FieldRow label="Staff discount (basis pts)">
          <NumInput value={data.staff_discount_percent_bp} onChange={set("staff_discount_percent_bp")} disabled={locked} />
        </FieldRow>
      )}
      <FieldRow label="Ministry discount">
        <Toggle value={data.ministry_discount_enabled} onChange={set("ministry_discount_enabled")} disabled={locked} />
      </FieldRow>
      {data.ministry_discount_enabled && (
        <FieldRow label="Ministry discount (basis pts)">
          <NumInput value={data.ministry_discount_percent_bp} onChange={set("ministry_discount_percent_bp")} disabled={locked} />
        </FieldRow>
      )}
      <FieldRow label="Max combined discount (bp)">
        <NumInput value={data.max_discount_percent_bp} onChange={set("max_discount_percent_bp")} disabled={locked} />
      </FieldRow>
    </StepCard>
  );
}

function StepAid({ data, onChange, locked }) {
  const set = (k) => (v) => onChange({ ...data, [k]: v });
  return (
    <StepCard label="Step 3 — Financial Aid Policy">
      <FieldRow label="Application fee">
        <MoneyCentsInput value={data.application_fee_cents} onChange={set("application_fee_cents")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Aid applies to">
        <Select
          value={data.aid_applies_to}
          onChange={set("aid_applies_to")}
          disabled={locked}
          options={[
            { value: "tuition_only", label: "Tuition only" },
            { value: "tuition_and_fees", label: "Tuition + Fees" },
          ]}
        />
      </FieldRow>
      <FieldRow label="Distribute aid evenly">
        <Toggle value={data.distribute_aid_evenly} onChange={set("distribute_aid_evenly")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Max aid per student" hint="0 = no cap">
        <MoneyCentsInput value={data.max_aid_per_student_cents} onChange={set("max_aid_per_student_cents")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Max aid per family" hint="0 = no cap">
        <MoneyCentsInput value={data.max_aid_per_family_cents} onChange={set("max_aid_per_family_cents")} disabled={locked} />
      </FieldRow>
    </StepCard>
  );
}

function StepPlans({ data, onChange, locked }) {
  const set = (k) => (v) => onChange({ ...data, [k]: v });
  return (
    <StepCard label="Step 4 — Payment Plans">
      {[
        ["allow_pay_in_full", "Pay in full"],
        ["allow_semi_annual", "Semi-annual (2 payments)"],
        ["allow_quarterly", "Quarterly (4 payments)"],
        ["allow_10_month", "10-month plan"],
        ["allow_12_month", "12-month plan"],
      ].map(([key, label]) => (
        <FieldRow key={key} label={label}>
          <Toggle value={data[key]} onChange={set(key)} disabled={locked} />
        </FieldRow>
      ))}
      <FieldRow label="ACH required for installments">
        <Toggle value={data.ach_required_for_installments} onChange={set("ach_required_for_installments")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Pay-in-full discount (bp)">
        <NumInput value={data.pay_in_full_discount_percent_bp} onChange={set("pay_in_full_discount_percent_bp")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Late fee grace days">
        <NumInput value={data.late_fee_grace_days} onChange={set("late_fee_grace_days")} disabled={locked} min={0} />
      </FieldRow>
      <FieldRow label="Late fee (flat)">
        <MoneyCentsInput value={data.late_fee_flat_cents} onChange={set("late_fee_flat_cents")} disabled={locked} />
      </FieldRow>
    </StepCard>
  );
}

function StepExtendedCare({ data, onChange, locked }) {
  const set = (k) => (v) => onChange({ ...data, [k]: v });
  return (
    <StepCard label="Step 5 — Extended Care / Before & After School">
      {[
        ["supports_annual", "Annual plan"],
        ["supports_monthly", "Monthly plan"],
        ["supports_weekly", "Weekly plan"],
        ["supports_drop_in_daily", "Drop-in daily"],
        ["supports_hybrid", "Hybrid plan"],
      ].map(([key, label]) => (
        <FieldRow key={key} label={label}>
          <Toggle value={data[key]} onChange={set(key)} disabled={locked} />
        </FieldRow>
      ))}
      <FieldRow label="Late pickup grace (min)">
        <NumInput value={data.late_pickup_grace_minutes} onChange={set("late_pickup_grace_minutes")} disabled={locked} min={0} />
      </FieldRow>
      <FieldRow label="Late pickup flat fee">
        <MoneyCentsInput value={data.late_pickup_fee_cents} onChange={set("late_pickup_fee_cents")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Late pickup per-minute fee">
        <MoneyCentsInput value={data.late_pickup_per_minute_cents} onChange={set("late_pickup_per_minute_cents")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Post to ledger automatically">
        <Toggle value={data.post_to_ledger} onChange={set("post_to_ledger")} disabled={locked} />
      </FieldRow>
      <FieldRow label="Include in tuition plan">
        <Toggle value={data.include_in_tuition_plan} onChange={set("include_in_tuition_plan")} disabled={locked} />
      </FieldRow>
    </StepCard>
  );
}

function StepReview({ academicYear, policy, locked, onSave, onLock, saving, locking, error, success }) {
  return (
    <StepCard label={`Step 6 — Review & ${locked ? "Snapshot" : "Lock"}`}>
      <p style={{ fontSize: 13, color: "var(--crown-ink)", marginBottom: 16 }}>
        Academic year: <strong>{academicYear}</strong>&nbsp;
        {locked && (
          <span style={{ color: "var(--crown-danger)", fontWeight: 600 }}>
            ? LOCKED — read only
          </span>
        )}
      </p>

      {error && (
        <div
          style={{
            background: "var(--crown-danger-bg)",
            border: "1px solid var(--crown-danger)",
            borderRadius: 6,
            padding: "10px 14px",
            fontSize: 13,
            color: "var(--crown-danger)",
            marginBottom: 14,
          }}
        >
          {error}
        </div>
      )}
      {success && (
        <div
          style={{
            background: "var(--crown-ok-bg)",
            border: "1px solid var(--crown-ok)",
            borderRadius: 6,
            padding: "10px 14px",
            fontSize: 13,
            color: "var(--crown-ok)",
            marginBottom: 14,
          }}
        >
          {success}
        </div>
      )}

      {!locked && (
        <div style={{ display: "flex", gap: 12 }}>
          <button
            onClick={onSave}
            disabled={saving}
            style={{
              background: "var(--crown-brand)",
              color: "var(--crown-surface)",
              border: "none",
              borderRadius: 6,
              padding: "9px 20px",
              fontSize: 13,
              fontWeight: 600,
              cursor: saving ? "default" : "pointer",
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? "Saving…" : "Save Draft"}
          </button>
          <button
            onClick={onLock}
            disabled={locking}
            style={{
              background: "var(--crown-danger)",
              color: "var(--crown-surface)",
              border: "none",
              borderRadius: 6,
              padding: "9px 20px",
              fontSize: 13,
              fontWeight: 600,
              cursor: locking ? "default" : "pointer",
              opacity: locking ? 0.6 : 1,
            }}
          >
            {locking ? "Locking…" : "Lock Policy (irreversible)"}
          </button>
        </div>
      )}

      {locked && (
        <div style={{ fontSize: 13, color: "var(--crown-muted)" }}>
          This policy is permanently locked. Contact your system administrator to start a new academic year.
        </div>
      )}

      {policy && (
        <details style={{ marginTop: 20 }}>
          <summary style={{ cursor: "pointer", fontSize: 12, color: "var(--crown-muted)" }}>
            Full snapshot (JSON)
          </summary>
          <pre
            style={{
              background: "var(--crown-surface-2)",
              border: "1px solid var(--crown-border)",
              borderRadius: 6,
              padding: 14,
              fontSize: 11,
              overflowX: "auto",
              marginTop: 8,
            }}
          >
            {JSON.stringify(policy, null, 2)}
          </pre>
        </details>
      )}
    </StepCard>
  );
}

// -- Step tab nav --------------------------------------------------------------

const STEPS = ["Tuition", "Discounts", "Aid", "Plans", "Extended Care", "Review & Lock"];

function StepNav({ current, onSelect }) {
  return (
    <div style={{ display: "flex", gap: 4, marginBottom: 24, flexWrap: "wrap" }}>
      {STEPS.map((label, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(idx)}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            border: "1px solid",
            borderColor: idx === current ? "var(--crown-brand)" : "var(--crown-border)",
            background: idx === current ? "var(--crown-brand)" : "var(--crown-surface)",
            color: idx === current ? "var(--crown-surface)" : "var(--crown-ink)",
            fontSize: 12,
            fontWeight: idx === current ? 600 : 400,
            cursor: "pointer",
          }}
        >
          {idx + 1}. {label}
        </button>
      ))}
    </div>
  );
}

// -- Main component ------------------------------------------------------------

const DEFAULT_YEAR = "2026-2027";

export default function FinanceSetupWizard() {
  const [academicYear] = useState(DEFAULT_YEAR);
  const [step, setStep] = useState(0);
  const [wizardData, setWizardData] = useState(defaults());
  const [locked, setLocked] = useState(false);
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locking, setLocking] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load existing policy on mount
  useEffect(() => {
    (async () => {
      try {
        const result = await fetchFinanceStatus(academicYear);
        if (result?.data) {
          const d = result.data;
          setSnapshot(d);
          setLocked(d.version?.is_locked ?? false);
          setWizardData({
            tuition: d.tuition ?? defaults().tuition,
            discounts: d.discounts ?? defaults().discounts,
            aid: d.aid ?? defaults().aid,
            payment_plans: d.payment_plans ?? defaults().payment_plans,
            extended_care: d.extended_care ?? defaults().extended_care,
          });
        }
      } catch {
        // Non-fatal: wizard starts with defaults
      } finally {
        setLoading(false);
      }
    })();
  }, [academicYear]);

  function setSection(key) {
    return (val) => setWizardData((prev) => ({ ...prev, [key]: val }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = { academic_year: academicYear, ...wizardData };
      const result = await saveFinancePolicy(payload);
      setSnapshot(result.data);
      setSuccess("Policy saved successfully.");
    } catch (e) {
      setError(e.status === 409 ? "Policy is locked — no changes allowed." : e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleLock() {
    if (
      !window.confirm(
        `Lock the ${academicYear} finance policy? This is permanent and cannot be undone.`
      )
    )
      return;

    setLocking(true);
    setError(null);
    setSuccess(null);
    try {
      // Save first, then lock
      const payload = { academic_year: academicYear, ...wizardData };
      await saveFinancePolicy(payload);
      const lockResult = await lockFinancePolicy(academicYear, "wizard-ui");
      setLocked(true);
      setSuccess(`Policy locked at ${lockResult.locked_at ?? "now"}.`);
    } catch (e) {
      setError(e.message);
    } finally {
      setLocking(false);
    }
  }

  if (loading) {
    return (
      <WizardShell title="Finance Setup Wizard">
        <p style={{ color: "var(--crown-muted)", fontSize: 14 }}>Loading policy…</p>
      </WizardShell>
    );
  }

  return (
    <WizardShell title={`Finance Setup Wizard — ${academicYear}`}>
      {locked && (
        <div
          style={{
            background: "var(--crown-danger-bg)",
            border: "1px solid var(--crown-danger)",
            borderRadius: 6,
            padding: "10px 16px",
            fontSize: 13,
            color: "var(--crown-danger)",
            marginBottom: 20,
            fontWeight: 600,
          }}
        >
          ? This policy is LOCKED. All fields are read-only.
        </div>
      )}

      <StepNav current={step} onSelect={setStep} />

      {step === 0 && (
        <StepTuition data={wizardData.tuition} onChange={setSection("tuition")} locked={locked} />
      )}
      {step === 1 && (
        <StepDiscounts data={wizardData.discounts} onChange={setSection("discounts")} locked={locked} />
      )}
      {step === 2 && (
        <StepAid data={wizardData.aid} onChange={setSection("aid")} locked={locked} />
      )}
      {step === 3 && (
        <StepPlans data={wizardData.payment_plans} onChange={setSection("payment_plans")} locked={locked} />
      )}
      {step === 4 && (
        <StepExtendedCare data={wizardData.extended_care} onChange={setSection("extended_care")} locked={locked} />
      )}
      {step === 5 && (
        <StepReview
          academicYear={academicYear}
          policy={snapshot}
          locked={locked}
          onSave={handleSave}
          onLock={handleLock}
          saving={saving}
          locking={locking}
          error={error}
          success={success}
        />
      )}

      {/* Prev/Next navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          style={{
            padding: "7px 18px",
            border: "1px solid var(--crown-border)",
            borderRadius: 6,
            background: "var(--crown-surface)",
            fontSize: 13,
            cursor: step === 0 ? "default" : "pointer",
            opacity: step === 0 ? 0.4 : 1,
          }}
        >
          ? Previous
        </button>
        <button
          onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
          disabled={step === STEPS.length - 1}
          style={{
            padding: "7px 18px",
            border: "1px solid var(--crown-border)",
            borderRadius: 6,
            background: "var(--crown-surface)",
            fontSize: 13,
            cursor: step === STEPS.length - 1 ? "default" : "pointer",
            opacity: step === STEPS.length - 1 ? 0.4 : 1,
          }}
        >
          Next ?
        </button>
      </div>
    </WizardShell>
  );
}

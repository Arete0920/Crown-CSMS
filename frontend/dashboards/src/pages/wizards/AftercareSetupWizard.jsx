import { useState } from "react";
import { Box, TextField, Typography, Alert, CircularProgress } from "@mui/material";
import CrownWizardStepper from "../../components/wizard/CrownWizardStepper.jsx";
import { fetchWizardConfig, submitWizardConfig } from "../../api/aftercareApi.js";
import { useEffect } from "react";

function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}

const STEPS = [
  "Program Hours & Fees",
  "Staffing Ratios",
  "Billing Defaults",
  "Review & Save",
];

// Shared text field wrapper
function Field({ label, value, onChange, type = "text", helperText }) {
  return (
    <TextField
      fullWidth
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      type={type}
      helperText={helperText}
      size="small"
      sx={{ mb: 2 }}
    />
  );
}

export default function AftercareSetupWizard() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [cfg, setCfg] = useState({
    start_time: "15:00:00",
    end_time: "18:00:00",
    late_fee_per_10_min: "10.00",
    late_fee_grace_minutes: "0",
    late_fee_cap: "100.00",
    ratio_k_2: "12",
    ratio_3_5: "15",
    ratio_6_8: "18",
    ratio_9_12: "20",
    default_billing_model: "FLAT_MONTHLY",
    dropin_daily_rate: "15.00",
    monthly_rate_1_day: "60.00",
    monthly_rate_2_days: "105.00",
    monthly_rate_3_days: "145.00",
    monthly_rate_4_days: "180.00",
    monthly_rate_5_days: "210.00",
  });

  function set(field) {
    return (val) => setCfg((prev) => ({ ...prev, [field]: val }));
  }

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchWizardConfig();
        const remote = res.config || {};
        setCfg((prev) => ({
          ...prev,
          ...Object.fromEntries(
            Object.entries(remote).filter(([k]) => k in prev).map(([k, v]) => [k, String(v)])
          ),
        }));
      } catch {
        // pre-population failure is non-fatal; user can type values manually
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await submitWizardConfig({ config: cfg });
      setSuccess(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <Box sx={{ p: 4, display: "flex", justifyContent: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (success) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="success">Aftercare program configured successfully!</Alert>
      </Box>
    );
  }

  // Panel 0: Hours & Late Fees
  const panel0 = (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>Program Hours & Late Fee Policy</Typography>
      <Field label="Start Time (HH:MM:SS)" value={cfg.start_time} onChange={set("start_time")} />
      <Field label="End Time (HH:MM:SS)" value={cfg.end_time} onChange={set("end_time")} />
      <Field label="Late Fee per 10 min ($)" value={cfg.late_fee_per_10_min} onChange={set("late_fee_per_10_min")} type="number" />
      <Field label="Grace Minutes (no charge window)" value={cfg.late_fee_grace_minutes} onChange={set("late_fee_grace_minutes")} type="number" />
      <Field label="Late Fee Cap ($)" value={cfg.late_fee_cap} onChange={set("late_fee_cap")} type="number" />
    </Box>
  );

  // Panel 1: Staffing Ratios
  const panel1 = (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>Staffing Ratios (students per staff)</Typography>
      <Field label="K-2 Ratio" value={cfg.ratio_k_2} onChange={set("ratio_k_2")} type="number" />
      <Field label="3-5 Ratio" value={cfg.ratio_3_5} onChange={set("ratio_3_5")} type="number" />
      <Field label="6-8 Ratio" value={cfg.ratio_6_8} onChange={set("ratio_6_8")} type="number" />
      <Field label="9-12 Ratio" value={cfg.ratio_9_12} onChange={set("ratio_9_12")} type="number" />
    </Box>
  );

  // Panel 2: Billing Defaults
  const panel2 = (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>Billing Defaults</Typography>
      <Field label="Drop-in Daily Rate ($)" value={cfg.dropin_daily_rate} onChange={set("dropin_daily_rate")} type="number" />
      <Field label="Monthly 1-Day Rate ($)" value={cfg.monthly_rate_1_day} onChange={set("monthly_rate_1_day")} type="number" />
      <Field label="Monthly 2-Day Rate ($)" value={cfg.monthly_rate_2_days} onChange={set("monthly_rate_2_days")} type="number" />
      <Field label="Monthly 3-Day Rate ($)" value={cfg.monthly_rate_3_days} onChange={set("monthly_rate_3_days")} type="number" />
      <Field label="Monthly 4-Day Rate ($)" value={cfg.monthly_rate_4_days} onChange={set("monthly_rate_4_days")} type="number" />
      <Field label="Monthly 5-Day Rate ($)" value={cfg.monthly_rate_5_days} onChange={set("monthly_rate_5_days")} type="number" />
    </Box>
  );

  // Panel 3: Review
  const panel3 = (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>Review Configuration</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {saving && <CircularProgress size={20} sx={{ mb: 2 }} />}
      <Typography variant="body2" component="pre" sx={{ fontFamily: "monospace", whiteSpace: "pre-wrap", fontSize: 12 }}>
        {JSON.stringify(cfg, null, 2)}
      </Typography>
    </Box>
  );

  return (
    <Box sx={{ maxWidth: 600, mx: "auto", mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>Aftercare Setup Wizard</Typography>
      <CrownWizardStepper steps={STEPS} onFinish={save}>
        {panel0}
        {panel1}
        {panel2}
        {panel3}
      </CrownWizardStepper>
    </Box>
  );
}

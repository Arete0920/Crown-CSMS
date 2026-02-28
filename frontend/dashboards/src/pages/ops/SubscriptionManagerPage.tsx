/**
 * SubscriptionManagerPage.tsx
 *
 * Platform Ops — Subscription Manager.
 * Allows super-admins to view and update a school tenant's active plan.
 *
 * Routes:
 *   GET  /api/v1/subscriptions/plans/           — list all available plans
 *   GET  /api/v1/subscriptions/ops/<school_id>/ — load current subscription
 *   POST /api/v1/subscriptions/ops/<school_id>/ — assign new plan
 *
 * Access: IsAdminUser (is_staff=true) — enforced at the API layer.
 */
import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControlLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";

import { apiFetch } from "../../lib/api";

type Plan = {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
  base_monthly: string | null;
};

type TenantSub = {
  id: number;
  school_id: string;
  plan: Plan;
  is_trial: boolean;
  started_at: string;
  ended_at: string | null;
};

const PLAN_COLOR: Record<string, "default" | "primary" | "success"> = {
  smart_start: "default",
  next_level: "primary",
  all_access: "success",
};

export default function SubscriptionManagerPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [plansError, setPlansError] = useState("");

  const [schoolId, setSchoolId] = useState("");
  const [sub, setSub] = useState<TenantSub | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(false);

  const [planId, setPlanId] = useState<number | "">("");
  const [isTrial, setIsTrial] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load plans on mount
  useEffect(() => {
    apiFetch("/api/v1/subscriptions/plans/")
      .then((data: Plan[]) => setPlans(data))
      .catch(() => setPlansError("Failed to load plans."));
  }, []);

  async function loadSub() {
    if (!schoolId.trim()) return;
    setLoading(true);
    setLoadError("");
    setSub(null);
    setSaveSuccess(false);
    try {
      const data = await apiFetch(`/api/v1/subscriptions/ops/${schoolId.trim()}/`);
      setSub(data as TenantSub);
      setPlanId((data as TenantSub).plan.id);
      setIsTrial((data as TenantSub).is_trial);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Not found or access denied.";
      setLoadError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function saveSub() {
    if (!schoolId.trim() || planId === "") return;
    setSaving(true);
    setSaveError("");
    setSaveSuccess(false);
    try {
      const data = await apiFetch(`/api/v1/subscriptions/ops/${schoolId.trim()}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId, is_trial: isTrial }),
      });
      setSub(data as TenantSub);
      setSaveSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save.";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", mt: 4, mb: 8 }}>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Subscription Manager
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Super-admin only. Enter a school UUID to view or update its active plan.
      </Typography>

      {plansError && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {plansError}
        </Alert>
      )}

      {/* School ID lookup */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" gutterBottom>
            School Tenant UUID
          </Typography>
          <Stack direction="row" spacing={1} alignItems="flex-start">
            <TextField
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
              placeholder="e.g. 00000000-0000-0000-0000-000000000000"
              fullWidth
              size="small"
              onKeyDown={(e) => e.key === "Enter" && loadSub()}
            />
            <Button
              variant="contained"
              onClick={loadSub}
              disabled={!schoolId.trim() || loading}
              sx={{ whiteSpace: "nowrap" }}
            >
              {loading ? <CircularProgress size={18} /> : "Load"}
            </Button>
          </Stack>
          {loadError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {loadError}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Current subscription + edit */}
      {sub && (
        <Card variant="outlined">
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                Current Subscription
              </Typography>
              <Chip
                label={sub.plan.code}
                color={PLAN_COLOR[sub.plan.code] ?? "default"}
                size="small"
                variant="outlined"
              />
            </Stack>

            <Stack spacing={0.5} sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Plan:</strong> {sub.plan.name}
              </Typography>
              <Typography variant="body2">
                <strong>Trial:</strong> {sub.is_trial ? "Yes" : "No"}
              </Typography>
              <Typography variant="body2">
                <strong>Started:</strong> {new Date(sub.started_at).toLocaleString()}
              </Typography>
            </Stack>

            <Divider sx={{ mb: 2 }} />

            <Typography variant="subtitle2" gutterBottom>
              Change Plan
            </Typography>

            <Stack spacing={2}>
              <Select
                value={planId}
                onChange={(e) => setPlanId(Number(e.target.value))}
                fullWidth
                size="small"
                displayEmpty
              >
                <MenuItem value="" disabled>
                  Select a plan…
                </MenuItem>
                {plans.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name} {p.base_monthly ? `— $${p.base_monthly}/mo` : ""}
                  </MenuItem>
                ))}
              </Select>

              <FormControlLabel
                control={
                  <Switch
                    checked={isTrial}
                    onChange={(e) => setIsTrial(e.target.checked)}
                  />
                }
                label="Trial subscription"
              />

              {saveError && <Alert severity="error">{saveError}</Alert>}
              {saveSuccess && (
                <Alert severity="success">Plan updated successfully.</Alert>
              )}

              <Button
                variant="contained"
                onClick={saveSub}
                disabled={saving || planId === ""}
              >
                {saving ? <CircularProgress size={18} /> : "Save"}
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

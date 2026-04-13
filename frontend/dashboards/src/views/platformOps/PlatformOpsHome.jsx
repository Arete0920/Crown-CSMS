/**
 * PlatformOpsHome.jsx
 *
 * Platform Operations Console — Super-Admin view.
 *
 * Displays a searchable, paginated list of all school tenants with their
 * TenantProfile status (slug, plan, status, payment provider).
 *
 * Accessible only to users with is_staff=true / IsAdminUser permission.
 * Does NOT require or send X-School-ID — these are cross-tenant ops.
 *
 * Dependencies: @mui/material, @mui/x-data-grid, axios (all already in use
 * elsewhere in the Crown2026 frontend).
 */
import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Select,
  Stack,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import axios from "axios";

// ─── Status chip colour map ───────────────────────────────────────────────────
const STATUS_COLOR = {
  pending: "warning",
  provisioning: "info",
  active: "success",
  suspended: "error",
  offboarded: "default",
};

// ─── DataGrid column definitions ─────────────────────────────────────────────
const columns = [
  {
    field: "slug",
    headerName: "Slug",
    width: 180,
    renderCell: ({ value }) => (
      <Typography variant="body2" fontFamily="monospace">
        {value}
      </Typography>
    ),
  },
  { field: "school_name", headerName: "School Name", flex: 1, minWidth: 200 },
  {
    field: "status",
    headerName: "Status",
    width: 130,
    renderCell: ({ value }) => (
      <Chip
        label={value}
        color={STATUS_COLOR[value] ?? "default"}
        size="small"
        variant="outlined"
      />
    ),
  },
  { field: "plan_code", headerName: "Plan", width: 110 },
  { field: "payment_provider", headerName: "Payments", width: 130 },
  { field: "timezone", headerName: "Timezone", width: 160 },
  {
    field: "domain",
    headerName: "Domain",
    width: 200,
    renderCell: ({ value }) =>
      value ? (
        <Typography variant="body2" color="text.secondary">
          {value}
        </Typography>
      ) : (
        <Typography variant="body2" color="text.disabled">
          —
        </Typography>
      ),
  },
  {
    field: "created_at",
    headerName: "Created",
    width: 180,
    renderCell: ({ value }) =>
      value ? new Date(value).toLocaleString() : "—",
  },
];

// ─── Create School Dialog ─────────────────────────────────────────────────────
function CreateSchoolDialog({ open, onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "",
    slug: "",
    domain: "",
    plan_code: "starter",
    timezone: "America/New_York",
    payment_provider: "none",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const idempotency_key = crypto.randomUUID();
      await axios.post("/api/platform/schools", { ...form, idempotency_key });
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create school.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create School Tenant</DialogTitle>
      <DialogContent>
        <Stack spacing={2} mt={1}>
          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}
          <TextField
            label="School Name"
            value={form.name}
            onChange={handleChange("name")}
            required
            fullWidth
          />
          <TextField
            label="Slug"
            value={form.slug}
            onChange={handleChange("slug")}
            required
            fullWidth
            helperText="URL-safe identifier, globally unique (e.g. lincoln-academy)"
          />
          <TextField
            label="Custom Domain"
            value={form.domain}
            onChange={handleChange("domain")}
            fullWidth
            placeholder="e.g. portal.lincolnacademy.org"
          />
          <Select
            value={form.plan_code}
            onChange={handleChange("plan_code")}
            fullWidth
          >
            <MenuItem value="starter">Starter</MenuItem>
            <MenuItem value="growth">Growth</MenuItem>
            <MenuItem value="enterprise">Enterprise</MenuItem>
          </Select>
          <TextField
            label="Timezone"
            value={form.timezone}
            onChange={handleChange("timezone")}
            fullWidth
            helperText="IANA timezone string"
          />
          <Select
            value={form.payment_provider}
            onChange={handleChange("payment_provider")}
            fullWidth
          >
            <MenuItem value="none">None / Manual</MenuItem>
            <MenuItem value="stripe">Stripe Connect</MenuItem>
            <MenuItem value="manual">Manual Invoice</MenuItem>
          </Select>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !form.name || !form.slug}
        >
          {loading ? <CircularProgress size={20} /> : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function PlatformOpsHome() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0); // DataGrid is 0-based
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchSchools = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = {
        page: page + 1, // API is 1-based
        per_page: pageSize,
      };
      if (statusFilter) params.status = statusFilter;

      const { data } = await axios.get("/api/platform/schools/list", { params });
      setRows(
        data.results.map((r) => ({ id: r.school_id, ...r }))
      );
      setTotal(data.total);
    } catch (err) {
      setError("Failed to load schools. Make sure you have super-admin access.");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter]);

  useEffect(() => {
    fetchSchools();
  }, [fetchSchools]);

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 6 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h5" fontWeight={700}>
            Platform Operations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Super-admin console — all school tenants across the platform.
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Refresh">
            <Button variant="outlined" onClick={fetchSchools} startIcon={<span aria-hidden="true">↻</span>}>
              Refresh
            </Button>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<span aria-hidden="true">＋</span>}
            onClick={() => setDialogOpen(true)}
          >
            Create School
          </Button>
        </Stack>
      </Stack>

      {/* Filters */}
      <Toolbar disableGutters sx={{ mb: 1, gap: 2 }}>
        <Select
          size="small"
          displayEmpty
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(0);
          }}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All Statuses</MenuItem>
          <MenuItem value="pending">Pending</MenuItem>
          <MenuItem value="provisioning">Provisioning</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="suspended">Suspended</MenuItem>
          <MenuItem value="offboarded">Offboarded</MenuItem>
        </Select>
        {error && (
          <Typography variant="body2" color="error">
            {error}
          </Typography>
        )}
      </Toolbar>

      {/* Data Grid */}
      <Box sx={{ height: 640, width: "100%" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          rowCount={total}
          loading={loading}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={({ page: p, pageSize: ps }) => {
            setPage(p);
            setPageSize(ps);
          }}
          pageSizeOptions={[25, 50, 100, 200]}
          disableRowSelectionOnClick
          density="compact"
          sx={{
            "& .MuiDataGrid-row:hover": { backgroundColor: "action.hover" },
          }}
        />
      </Box>

      {/* Create school dialog */}
      <CreateSchoolDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={fetchSchools}
      />
    </Container>
  );
}

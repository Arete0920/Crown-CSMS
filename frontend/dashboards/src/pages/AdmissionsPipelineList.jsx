import { useMemo, useState } from 'react';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getAdmissionsApplications, enrollApplicant } from '../api/admissions';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';
import { useApiAction } from '../hooks/useApiAction';

const STATUS_LABELS = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  UNDER_REVIEW: 'Under review',
  NEEDS_INFO: 'Needs info',
  ACCEPTED: 'Accepted',
  WAITLISTED: 'Waitlisted',
  DENIED: 'Denied',
  WITHDRAWN: 'Withdrawn',
  ENROLLED: 'Enrolled',
};

export function AdmissionsPipelineList() {
  const [selected, setSelected] = useState(null);
  const [enrollResult, setEnrollResult] = useState(null);

  const {
    search,
    setSearch,
    filters,
    setFilter,
    clearFilters,
    page,
    setPage,
    rowsPerPage,
    setRowsPerPage,
  } = usePersistentTableState('admissions-pipeline-table', {
    search: '',
    filters: { status: '' },
    page: 0,
    rowsPerPage: 10,
  });

  const { loading, error, data, reload } = useAsyncPageData(async () => {
    const source = await getAdmissionsApplications();
    return (source || []).map((app) => ({
      id: app.id,
      applicant_name: app.applicant_name || '',
      student_first_name: app.student_first_name || '',
      student_last_name: app.student_last_name || '',
      status: app.status || 'DRAFT',
      household_name: app.household_name || '',
      created_at: app.created_at || '',
      updated_at: app.updated_at || '',
    }));
  }, []);

  const { run: runEnroll, loading: enrolling, error: enrollError } = useApiAction(
    async (applicationId) => {
      return enrollApplicant(applicationId);
    },
  );

  const rows = useMemo(() => {
    const source = Array.isArray(data) ? data : [];

    return source.filter((row) => {
      const searchBlob = `${row.applicant_name} ${row.student_first_name} ${row.student_last_name} ${row.household_name}`
        .toLowerCase();
      const matchesSearch = !search || searchBlob.includes(search.toLowerCase());
      const matchesStatus = !filters.status || row.status === filters.status;
      return matchesSearch && matchesStatus;
    });
  }, [data, search, filters.status]);

  const columns = [
    { key: 'applicant_name', label: 'Applicant', sortable: true },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (row) => STATUS_LABELS[row.status] || row.status,
    },
    { key: 'household_name', label: 'Household', sortable: true },
    {
      key: 'created_at',
      label: 'Submitted',
      sortable: true,
      render: (row) => (row.created_at ? new Date(row.created_at).toLocaleDateString() : '—'),
    },
    {
      key: 'updated_at',
      label: 'Updated',
      sortable: true,
      render: (row) => (row.updated_at ? new Date(row.updated_at).toLocaleDateString() : '—'),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (row) => (
        <Button size="small" onClick={() => setSelected(row)}>
          Open
        </Button>
      ),
    },
  ];

  const filterControls = (
    <Stack direction="row" spacing={1}>
      <Button
        size="small"
        variant={filters.status === '' ? 'contained' : 'outlined'}
        onClick={() => setFilter('status', '')}
      >
        All
      </Button>
      <Button
        size="small"
        variant={filters.status === 'SUBMITTED' ? 'contained' : 'outlined'}
        onClick={() => setFilter('status', 'SUBMITTED')}
      >
        Submitted
      </Button>
      <Button
        size="small"
        variant={filters.status === 'ACCEPTED' ? 'contained' : 'outlined'}
        onClick={() => setFilter('status', 'ACCEPTED')}
      >
        Accepted
      </Button>
    </Stack>
  );

  const actions = (
    <Stack direction="row" spacing={1}>
      <Button
        variant="outlined"
        onClick={() => {
          const header = ['Applicant', 'Status', 'Household', 'Submitted', 'Updated'];
          const lines = [header.map(csvEscape).join(',')];
          for (const app of rows) {
            lines.push(
              [
                app.applicant_name,
                STATUS_LABELS[app.status] || app.status,
                app.household_name,
                app.created_at ? new Date(app.created_at).toLocaleDateString() : '',
                app.updated_at ? new Date(app.updated_at).toLocaleDateString() : '',
              ]
                .map(csvEscape)
                .join(','),
            );
          }
          downloadTextFile('admissions_pipeline.csv', lines.join('\n'));
        }}
      >
        Export CSV
      </Button>
      <Button variant="outlined" onClick={clearFilters}>
        Clear Filters
      </Button>
      <Button variant="outlined" onClick={reload}>
        Reload
      </Button>
    </Stack>
  );

  async function handleEnrollSelected() {
    if (!selected) return;
    setEnrollResult(null);

    try {
      const result = await runEnroll(selected.id);
      setEnrollResult({ ok: true, message: result.message || 'Applicant enrolled.' });
      await reload();
    } catch {
      setEnrollResult({ ok: false, message: 'Unable to enroll applicant.' });
    }
  }

  return (
    <CrownLayout title="Admissions Pipeline" subtitle="Applicant tracking and enrollment">
      <CrownDataTable
        title="Applications"
        subtitle="Pipeline view with standardized sorting and pagination"
        rows={rows}
        columns={columns}
        loading={loading}
        error={error}
        searchValue={search}
        onSearchChange={setSearch}
        filters={filterControls}
        actions={actions}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        initialSortKey="updated_at"
        initialSortDirection="desc"
        emptyTitle="No applications"
        emptyMessage="Admissions applications will appear here once submitted."
      />

      {selected ? (
        <Drawer onClose={() => setSelected(null)} width={520}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
              Application Detail
            </Typography>

            {enrollResult ? (
              <Alert severity={enrollResult.ok ? 'success' : 'error'} sx={{ mb: 2 }}>
                {enrollResult.message}
              </Alert>
            ) : null}

            {enrollError ? (
              <Alert severity="error" sx={{ mb: 2 }}>
                {enrollError.message}
              </Alert>
            ) : null}

            <Stack spacing={1.25} sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Applicant:</strong> {selected.applicant_name}
              </Typography>
              <Typography variant="body2">
                <strong>Status:</strong> {STATUS_LABELS[selected.status] || selected.status}
              </Typography>
              <Typography variant="body2">
                <strong>Household:</strong> {selected.household_name || '—'}
              </Typography>
            </Stack>

            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                onClick={handleEnrollSelected}
                disabled={enrolling || selected.status === 'ENROLLED'}
              >
                {enrolling ? 'Enrolling...' : 'Enroll Applicant'}
              </Button>
              <Button variant="outlined" onClick={() => setSelected(null)}>
                Close
              </Button>
            </Stack>
          </Box>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

export default AdmissionsPipelineList;

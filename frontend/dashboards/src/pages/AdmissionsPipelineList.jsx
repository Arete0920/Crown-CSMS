import { useMemo, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getAdmissionsApplications, enrollApplicant } from '../api/admissions';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';
import { useApiAction } from '../hooks/useApiAction';

const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
const SM_ON = { ...SM, background: '#1976d2', color: '#fff' };
const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
const BTN_FILLED = { ...BTN, background: '#1976d2', color: '#fff' };
const ROW = { display: 'flex', gap: '8px', alignItems: 'center' };
const LABEL = { margin: 0, fontSize: '0.875rem' };

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
        <button type="button" style={SM} onClick={() => setSelected(row)}>Open</button>
      ),
    },
  ];

  const filterControls = (
    <div style={ROW}>
      <button type="button" style={filters.status === '' ? SM_ON : SM} onClick={() => setFilter('status', '')}>All</button>
      <button type="button" style={filters.status === 'SUBMITTED' ? SM_ON : SM} onClick={() => setFilter('status', 'SUBMITTED')}>Submitted</button>
      <button type="button" style={filters.status === 'ACCEPTED' ? SM_ON : SM} onClick={() => setFilter('status', 'ACCEPTED')}>Accepted</button>
    </div>
  );

  const actions = (
    <div style={ROW}>
      <button type="button" style={BTN} onClick={() => {
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
      }}>Export CSV</button>
      <button type="button" style={BTN} onClick={clearFilters}>Clear Filters</button>
      <button type="button" style={BTN} onClick={reload}>Reload</button>
    </div>
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
          <div style={{ padding: '24px' }}>
            <h6 style={{ margin: 0, marginBottom: '1rem', fontWeight: 700, fontSize: '1.25rem' }}>Application Detail</h6>

            {enrollResult ? (
              <div role="alert" style={{ padding: '8px 16px', borderRadius: '4px', background: enrollResult.ok ? '#e8f5e9' : '#ffebee', color: enrollResult.ok ? '#1b5e20' : '#b71c1c', border: `1px solid ${enrollResult.ok ? '#81c784' : '#ef9a9a'}`, marginBottom: '8px' }}>
                {enrollResult.message}
              </div>
            ) : null}

            {enrollError ? (
              <div role="alert" style={{ padding: '8px 16px', borderRadius: '4px', background: '#ffebee', color: '#b71c1c', border: '1px solid #ef9a9a', marginBottom: '8px' }}>
                {enrollError.message}
              </div>
            ) : null}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
              <p style={LABEL}><strong>Applicant:</strong> {selected.applicant_name}</p>
              <p style={LABEL}><strong>Status:</strong> {STATUS_LABELS[selected.status] || selected.status}</p>
              <p style={LABEL}><strong>Household:</strong> {selected.household_name || '—'}</p>
            </div>

            <div style={ROW}>
              <button type="button" style={BTN_FILLED} onClick={handleEnrollSelected} disabled={enrolling || selected.status === 'ENROLLED'}>
                {enrolling ? 'Enrolling...' : 'Enroll Applicant'}
              </button>
              <button type="button" style={BTN} onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

export default AdmissionsPipelineList;

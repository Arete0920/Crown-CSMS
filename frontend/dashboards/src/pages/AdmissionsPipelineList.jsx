import { useCallback, useMemo, useState } from 'react';
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

function mapAdmissionsApp(app) {
  return {
    id: app.id,
    applicant_name: app.applicant_name || '',
    student_first_name: app.student_first_name || '',
    student_last_name: app.student_last_name || '',
    status: app.status || 'DRAFT',
    household_id: app.household_id || '',
    household_name: app.household_name || '',
    created_at: app.created_at || '',
    updated_at: app.updated_at || '',
    guardian_contacts: Array.isArray(app.guardian_contacts) ? app.guardian_contacts : [],
    primary_guardian_name: app.primary_guardian_name || '',
    primary_guardian_email: app.primary_guardian_email || '',
    primary_guardian_phone: app.primary_guardian_phone || '',
  };
}

function getHouseholdApplications(selected, rows) {
  if (!selected) return [];
  const source = Array.isArray(rows) ? rows : [];
  const householdId = selected.household_id || '';
  const householdName = selected.household_name || '';

  const grouped = source.filter((row) => {
    if (householdId && row.household_id) {
      return row.household_id === householdId;
    }
    return householdName && row.household_name === householdName;
  });

  return grouped.length > 0 ? grouped : [selected];
}

function getContactRail(selected, householdApplications) {
  for (const app of householdApplications) {
    if (Array.isArray(app.guardian_contacts) && app.guardian_contacts.length > 0) {
      return app.guardian_contacts;
    }
  }

  if (!selected) return [];
  if (!(selected.primary_guardian_name || selected.primary_guardian_email || selected.primary_guardian_phone)) {
    return [];
  }

  return [
    {
      name: selected.primary_guardian_name,
      email: selected.primary_guardian_email,
      phone: selected.primary_guardian_phone,
      is_primary: true,
      role: 'PRIMARY_GUARDIAN',
    },
  ];
}

function HouseholdReviewDrawer({
  selected,
  setSelected,
  expandedChildren,
  setExpandedChildren,
  enrollResult,
  enrollError,
  enrolling,
  householdApplications,
  contactRail,
  onEnroll,
}) {
  if (!selected) return null;

  function toggleChildCard(applicationId) {
    setExpandedChildren((prev) => ({
      ...prev,
      [applicationId]: !prev[applicationId],
    }));
  }

  function closeDrawer() {
    setSelected(null);
    setExpandedChildren({});
  }

  return (
    <Drawer open={Boolean(selected)} onClose={closeDrawer} width={640}>
      <div style={{ padding: '24px' }}>
        <h6 style={{ margin: 0, marginBottom: '1rem', fontWeight: 700, fontSize: '1.25rem' }}>Household Admissions Review</h6>

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

        <div style={{ display: 'grid', gap: '12px', marginBottom: '20px' }}>
          <div style={{ border: '1px solid var(--crown-border)', borderRadius: 8, padding: 12, background: 'var(--crown-subtle)' }}>
            <p style={LABEL}><strong>Household:</strong> {selected.household_name || selected.applicant_name || '—'}</p>
            <p style={LABEL}><strong>Applications:</strong> {householdApplications.length}</p>
          </div>

          <div style={{ border: '1px solid var(--crown-border)', borderRadius: 8, padding: 12 }}>
            <p style={{ ...LABEL, marginBottom: 8 }}><strong>Guardian / Contact Rail</strong></p>
            {contactRail.length === 0 ? (
              <p style={LABEL}>No guardian contacts on file for this household.</p>
            ) : (
              <div style={{ display: 'grid', gap: 8 }}>
                {contactRail.map((contact, index) => (
                  <div key={`${contact.name}-${index}`} style={{ border: '1px solid var(--crown-border)', borderRadius: 6, padding: '8px 10px' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      {contact.name || 'Guardian'} {contact.is_primary ? '(Primary)' : ''}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--crown-muted)' }}>
                      {contact.email || 'No email'} · {contact.phone || 'No phone'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'grid', gap: 10, marginBottom: 16 }}>
          {householdApplications.map((appRow) => {
            const expanded = Boolean(expandedChildren[appRow.id]);
            const studentName = `${appRow.student_first_name || ''} ${appRow.student_last_name || ''}`.trim() || 'Student record pending';

            return (
              <div key={appRow.id} style={{ border: '1px solid var(--crown-border)', borderRadius: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 10, gap: 10 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{studentName}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--crown-muted)' }}>
                      {STATUS_LABELS[appRow.status] || appRow.status}
                    </div>
                  </div>
                  <button type="button" style={SM} onClick={() => toggleChildCard(appRow.id)}>
                    {expanded ? 'Hide details' : 'Show details'}
                  </button>
                </div>

                {expanded ? (
                  <div style={{ borderTop: '1px solid var(--crown-border)', padding: 10, display: 'grid', gap: 8 }}>
                    <p style={LABEL}><strong>Submitted:</strong> {appRow.created_at ? new Date(appRow.created_at).toLocaleString() : '—'}</p>
                    <p style={LABEL}><strong>Updated:</strong> {appRow.updated_at ? new Date(appRow.updated_at).toLocaleString() : '—'}</p>
                    <div style={ROW}>
                      <button
                        type="button"
                        style={BTN_FILLED}
                        onClick={() => onEnroll(appRow.id)}
                        disabled={enrolling || appRow.status === 'ENROLLED'}
                      >
                        {enrolling ? 'Enrolling...' : 'Enroll Child'}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        <div style={ROW}>
          <button type="button" style={BTN} onClick={closeDrawer}>Close</button>
        </div>
      </div>
    </Drawer>
  );
}

export function AdmissionsPipelineList() {
  const [selected, setSelected] = useState(null);
  const [expandedChildren, setExpandedChildren] = useState({});
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

  const loadAdmissionsApplications = useCallback(async () => {
    const source = await getAdmissionsApplications();
    return (source || []).map(mapAdmissionsApp);
  }, []);

  const { loading, error, data, reload } = useAsyncPageData(loadAdmissionsApplications, []);

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

  const householdApplications = useMemo(() => getHouseholdApplications(selected, rows), [rows, selected]);
  const contactRail = useMemo(() => getContactRail(selected, householdApplications), [householdApplications, selected]);

  async function handleEnrollSelected(applicationId) {
    if (!applicationId) return;
    setEnrollResult(null);

    try {
      const result = await runEnroll(applicationId);
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

      <HouseholdReviewDrawer
        selected={selected}
        setSelected={setSelected}
        expandedChildren={expandedChildren}
        setExpandedChildren={setExpandedChildren}
        enrollResult={enrollResult}
        enrollError={enrollError}
        enrolling={enrolling}
        householdApplications={householdApplications}
        contactRail={contactRail}
        onEnroll={handleEnrollSelected}
      />
    </CrownLayout>
  );
}

export default AdmissionsPipelineList;

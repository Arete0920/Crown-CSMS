import { useMemo, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getThreads, getThreadDetail } from '../api/communications';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';

const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--crown-compat-color-cb69c739b8)', background: 'transparent', color: 'var(--crown-compat-color-cb69c739b8)' };
const SM_ON = { ...SM, background: 'var(--crown-compat-color-cb69c739b8)', color: 'var(--crown-compat-color-e08de71387)' };
const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--crown-compat-color-cb69c739b8)', background: 'transparent', color: 'var(--crown-compat-color-cb69c739b8)' };
const ROW = { display: 'flex', gap: '8px', alignItems: 'center' };
const LABEL = { margin: 0, fontSize: '0.875rem' };

function formatDateTime(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return '—';
  }
}

export default function CommunicationsThreadsList() {
  const [selected, setSelected] = useState(null);

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
  } = usePersistentTableState('communications-threads-table', {
    search: '',
    filters: { threadType: '' },
    page: 0,
    rowsPerPage: 10,
  });

  const { loading, error, data, reload } = useAsyncPageData(async () => {
    const threads = await getThreads();
    return (threads || []).map((thread) => ({
      id: thread.thread_id,
      household_name: thread.household_name || '(No household)',
      student_name:
        thread.student_first_name && thread.student_last_name
          ? `${thread.student_first_name} ${thread.student_last_name}`
          : '',
      subject: thread.subject || '(No subject)',
      thread_type: thread.thread_type || 'GENERAL',
      last_message_at: thread.last_message_at || null,
    }));
  }, []);

  const {
    loading: loadingThread,
    error: threadError,
    data: threadDetail,
  } = useAsyncPageData(
    async () => {
      if (!selected?.id) return null;
      return getThreadDetail(selected.id);
    },
    [selected?.id],
  );

  const rows = useMemo(() => {
    const source = Array.isArray(data) ? data : [];

    return source.filter((row) => {
      const searchBlob = `${row.household_name} ${row.student_name} ${row.subject}`.toLowerCase();
      const matchesSearch = !search || searchBlob.includes(search.toLowerCase());
      const matchesType = !filters.threadType || row.thread_type === filters.threadType;
      return matchesSearch && matchesType;
    });
  }, [data, search, filters.threadType]);

  const columns = [
    { key: 'household_name', label: 'Household', sortable: true },
    {
      key: 'student_name',
      label: 'Student',
      sortable: true,
      render: (row) => row.student_name || '(None)',
    },
    { key: 'subject', label: 'Subject', sortable: true },
    { key: 'thread_type', label: 'Type', sortable: true },
    {
      key: 'last_message_at',
      label: 'Last Message',
      sortable: true,
      render: (row) => formatDateTime(row.last_message_at),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (row) => (
        <button type="button" style={SM} onClick={() => setSelected(row)}>Open</button>
      ),
    },
  ];

  const uniqueTypes = useMemo(() => {
    const source = Array.isArray(data) ? data : [];
    return Array.from(new Set(source.map((item) => item.thread_type).filter(Boolean))).sort();
  }, [data]);

  const filterControls = (
    <div style={ROW}>
      <button type="button" style={filters.threadType === '' ? SM_ON : SM} onClick={() => setFilter('threadType', '')}>All</button>
      {uniqueTypes.slice(0, 3).map((threadType) => (
        <button key={threadType} type="button" style={filters.threadType === threadType ? SM_ON : SM} onClick={() => setFilter('threadType', threadType)}>{threadType}</button>
      ))}
    </div>
  );

  const actions = (
    <div style={ROW}>
      <button type="button" style={BTN} onClick={() => {
        const header = ['Household', 'Student', 'Subject', 'Type', 'Last Message'];
        const lines = [header.map(csvEscape).join(',')];
        for (const row of rows) {
          lines.push(
            [row.household_name, row.student_name, row.subject, row.thread_type, row.last_message_at || '']
              .map(csvEscape)
              .join(','),
          );
        }
        downloadTextFile('communications_threads.csv', lines.join('\n'));
      }}>Export CSV</button>
      <button type="button" style={BTN} onClick={clearFilters}>Clear Filters</button>
      <button type="button" style={BTN} onClick={reload}>Reload</button>
    </div>
  );

  return (
    <CrownLayout title="Communications — Threads" subtitle="Director inbox">
      <CrownDataTable
        title="Threads"
        subtitle="Standardized thread list"
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
        initialSortKey="last_message_at"
        initialSortDirection="desc"
        emptyTitle="No message threads"
        emptyMessage="Thread activity will appear here once communications are created."
      />

      {selected ? (
        <Drawer onClose={() => setSelected(null)} width={560}>
          <div style={{ padding: '24px' }}>
            <h6 style={{ margin: 0, marginBottom: '1rem', fontWeight: 700, fontSize: '1.25rem' }}>Thread Detail</h6>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
              <p style={LABEL}><strong>Subject:</strong> {selected.subject}</p>
              <p style={LABEL}><strong>Household:</strong> {selected.household_name}</p>
              <p style={LABEL}><strong>Student:</strong> {selected.student_name || '(None)'}</p>
              <p style={LABEL}><strong>Type:</strong> {selected.thread_type}</p>
            </div>

            {loadingThread ? (
              <p style={LABEL}>Loading messages...</p>
            ) : threadError ? (
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--crown-compat-color-589c0cbec4)' }}>
                {threadError?.message || 'Unable to load thread detail.'}
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {(threadDetail?.messages || []).slice(-10).map((message, index) => (
                  <div key={message.id || index} style={{ padding: '12px', borderRadius: '8px', backgroundColor: 'var(--crown-compat-color-f62328dee8)' }}>
                    <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>
                      {message.author_name || message.author || 'Sender'}
                    </p>
                    <p style={LABEL}>{message.body || message.message || '(No content)'}</p>
                    <span style={{ fontSize: '0.75rem', color: 'var(--crown-compat-color-81cbc44d1a)' }}>
                      {formatDateTime(message.created_at || message.sent_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: '16px' }}>
              <button type="button" style={BTN} onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

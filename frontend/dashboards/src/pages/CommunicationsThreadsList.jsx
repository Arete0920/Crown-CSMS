import { useMemo, useState } from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getThreads, getThreadDetail } from '../api/communications';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';

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
        <Button size="small" onClick={() => setSelected(row)}>
          Open
        </Button>
      ),
    },
  ];

  const uniqueTypes = useMemo(() => {
    const source = Array.isArray(data) ? data : [];
    return Array.from(new Set(source.map((item) => item.thread_type).filter(Boolean))).sort();
  }, [data]);

  const filterControls = (
    <Stack direction="row" spacing={1}>
      <Button
        size="small"
        variant={filters.threadType === '' ? 'contained' : 'outlined'}
        onClick={() => setFilter('threadType', '')}
      >
        All
      </Button>
      {uniqueTypes.slice(0, 3).map((threadType) => (
        <Button
          key={threadType}
          size="small"
          variant={filters.threadType === threadType ? 'contained' : 'outlined'}
          onClick={() => setFilter('threadType', threadType)}
        >
          {threadType}
        </Button>
      ))}
    </Stack>
  );

  const actions = (
    <Stack direction="row" spacing={1}>
      <Button
        variant="outlined"
        onClick={() => {
          const header = ['Household', 'Student', 'Subject', 'Type', 'Last Message'];
          const lines = [header.map(csvEscape).join(',')];

          for (const row of rows) {
            lines.push(
              [
                row.household_name,
                row.student_name,
                row.subject,
                row.thread_type,
                row.last_message_at || '',
              ]
                .map(csvEscape)
                .join(','),
            );
          }

          downloadTextFile('communications_threads.csv', lines.join('\n'));
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
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
              Thread Detail
            </Typography>

            <Stack spacing={1} sx={{ mb: 2 }}>
              <Typography variant="body2"><strong>Subject:</strong> {selected.subject}</Typography>
              <Typography variant="body2"><strong>Household:</strong> {selected.household_name}</Typography>
              <Typography variant="body2"><strong>Student:</strong> {selected.student_name || '(None)'}</Typography>
              <Typography variant="body2"><strong>Type:</strong> {selected.thread_type}</Typography>
            </Stack>

            {loadingThread ? (
              <Typography variant="body2">Loading messages...</Typography>
            ) : threadError ? (
              <Typography variant="body2" color="error.main">
                {threadError?.message || 'Unable to load thread detail.'}
              </Typography>
            ) : (
              <Stack spacing={1.25}>
                {(threadDetail?.messages || []).slice(-10).map((message, index) => (
                  <Box key={message.id || index} sx={{ p: 1.5, borderRadius: 2, bgcolor: 'grey.100' }}>
                    <Typography variant="body2" fontWeight={600}>
                      {message.author_name || message.author || 'Sender'}
                    </Typography>
                    <Typography variant="body2">{message.body || message.message || '(No content)'}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatDateTime(message.created_at || message.sent_at)}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            )}

            <Button sx={{ mt: 2 }} variant="outlined" onClick={() => setSelected(null)}>
              Close
            </Button>
          </Box>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

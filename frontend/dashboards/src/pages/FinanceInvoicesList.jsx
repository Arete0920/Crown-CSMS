import { useMemo, useState } from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getInvoices } from '../api/finance';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Number(value || 0));
}

export default function FinanceInvoicesList() {
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
  } = usePersistentTableState('finance-invoices-table', {
    search: '',
    filters: { delinquentOnly: '' },
    page: 0,
    rowsPerPage: 10,
  });

  const { loading, error, data, reload } = useAsyncPageData(async () => {
    const invoices = await getInvoices();
    return invoices.map((inv) => ({
      id: inv.id,
      household_name: inv.household_name || '(No household)',
      total_amount: parseFloat(inv.total_amount) || 0,
      paid_amount: parseFloat(inv.paid_amount) || 0,
      balance_due: parseFloat(inv.balance_due) || 0,
      credit_amount: parseFloat(inv.credit_amount) || 0,
      due_on: inv.due_on || null,
      days_past_due: Number.isFinite(inv.days_past_due) ? inv.days_past_due : 0,
      aging_bucket: inv.aging_bucket || 'current',
      is_delinquent: !!inv.is_delinquent,
      is_reversed: !!inv.is_reversed,
    }));
  }, []);

  const rows = useMemo(() => {
    const source = Array.isArray(data) ? data : [];

    return source.filter((row) => {
      const searchBlob = `${row.household_name} ${row.aging_bucket}`.toLowerCase();
      const matchesSearch = !search || searchBlob.includes(search.toLowerCase());
      const matchesDelinquent =
        filters.delinquentOnly !== 'true' ? true : row.is_delinquent;
      return matchesSearch && matchesDelinquent;
    });
  }, [data, search, filters.delinquentOnly]);

  const summary = useMemo(() => {
    const source = Array.isArray(data) ? data : [];
    const delinquentRows = source.filter((row) => row.is_delinquent);

    return {
      delinquentCount: delinquentRows.length,
      delinquentBalance: delinquentRows.reduce((sum, row) => sum + row.balance_due, 0),
      credits: source.reduce((sum, row) => sum + row.credit_amount, 0),
      reversedCount: source.filter((row) => row.is_reversed).length,
    };
  }, [data]);

  const columns = [
    { key: 'household_name', label: 'Payer', sortable: true },
    {
      key: 'total_amount',
      label: 'Total',
      sortable: true,
      render: (row) => formatCurrency(row.total_amount),
    },
    {
      key: 'paid_amount',
      label: 'Paid',
      sortable: true,
      render: (row) => formatCurrency(row.paid_amount),
    },
    {
      key: 'balance_due',
      label: 'Balance Due',
      sortable: true,
      render: (row) => formatCurrency(row.balance_due),
    },
    { key: 'days_past_due', label: 'Days Past Due', sortable: true },
    { key: 'aging_bucket', label: 'Aging Bucket', sortable: true },
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
        variant={filters.delinquentOnly !== 'true' ? 'contained' : 'outlined'}
        onClick={() => setFilter('delinquentOnly', '')}
      >
        All
      </Button>
      <Button
        size="small"
        variant={filters.delinquentOnly === 'true' ? 'contained' : 'outlined'}
        onClick={() => setFilter('delinquentOnly', 'true')}
      >
        Delinquent Only
      </Button>
    </Stack>
  );

  const actions = (
    <Stack direction="row" spacing={1}>
      <Button
        variant="outlined"
        onClick={() => {
          const header = [
            'Payer',
            'Total Amount',
            'Paid',
            'Balance Due',
            'Credit',
            'Days Past Due',
            'Aging Bucket',
          ];
          const lines = [header.map(csvEscape).join(',')];
          for (const row of rows) {
            lines.push(
              [
                row.household_name,
                row.total_amount.toFixed(2),
                row.paid_amount.toFixed(2),
                row.balance_due.toFixed(2),
                row.credit_amount.toFixed(2),
                String(row.days_past_due),
                row.aging_bucket,
              ]
                .map(csvEscape)
                .join(','),
            );
          }
          downloadTextFile('invoices.csv', lines.join('\n'));
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
    <CrownLayout title="Finance" subtitle="Invoice history and exports">
      <CrownDataTable
        title="Invoices"
        subtitle="Standardized invoice table"
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
        initialSortKey="days_past_due"
        initialSortDirection="desc"
        emptyTitle="No invoices found"
        emptyMessage="There are no invoice records matching the current filters."
      />

      <Box sx={{ mt: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <Typography variant="body2">Delinquent: <strong>{summary.delinquentCount}</strong></Typography>
          <Typography variant="body2">Past Due: <strong>{formatCurrency(summary.delinquentBalance)}</strong></Typography>
          <Typography variant="body2">Credits: <strong>{formatCurrency(summary.credits)}</strong></Typography>
          <Typography variant="body2">Reversals: <strong>{summary.reversedCount}</strong></Typography>
        </Stack>
      </Box>

      {selected ? (
        <Drawer onClose={() => setSelected(null)} width={500}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
              Invoice Detail
            </Typography>
            <Stack spacing={1.25}>
              <Typography variant="body2"><strong>Payer:</strong> {selected.household_name}</Typography>
              <Typography variant="body2"><strong>Total:</strong> {formatCurrency(selected.total_amount)}</Typography>
              <Typography variant="body2"><strong>Paid:</strong> {formatCurrency(selected.paid_amount)}</Typography>
              <Typography variant="body2"><strong>Balance:</strong> {formatCurrency(selected.balance_due)}</Typography>
              <Typography variant="body2"><strong>Aging:</strong> {selected.aging_bucket}</Typography>
            </Stack>
            <Button sx={{ mt: 2 }} variant="outlined" onClick={() => setSelected(null)}>
              Close
            </Button>
          </Box>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

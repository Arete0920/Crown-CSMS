import { useMemo, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownDataTable from '../components/data/CrownDataTable.jsx';
import Drawer from '../components/Drawer';
import { getInvoices } from '../api/finance';
import { csvEscape, downloadTextFile } from '../lib/export/csv';
import { useAsyncPageData } from '../hooks/useAsyncPageData';
import { usePersistentTableState } from '../hooks/usePersistentTableState';

const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--crown-compat-color-cb69c739b8)', background: 'transparent', color: 'var(--crown-compat-color-cb69c739b8)' };
const SM_ON = { ...SM, background: 'var(--crown-compat-color-cb69c739b8)', color: 'var(--crown-compat-color-e08de71387)' };
const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--crown-compat-color-cb69c739b8)', background: 'transparent', color: 'var(--crown-compat-color-cb69c739b8)' };
const ROW = { display: 'flex', gap: '8px', alignItems: 'center' };
const LABEL = { margin: 0, fontSize: '0.875rem' };

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
        <button type="button" style={SM} onClick={() => setSelected(row)}>Open</button>
      ),
    },
  ];

  const filterControls = (
    <div style={ROW}>
      <button type="button" style={filters.delinquentOnly !== 'true' ? SM_ON : SM} onClick={() => setFilter('delinquentOnly', '')}>All</button>
      <button type="button" style={filters.delinquentOnly === 'true' ? SM_ON : SM} onClick={() => setFilter('delinquentOnly', 'true')}>Delinquent Only</button>
    </div>
  );

  const actions = (
    <div style={ROW}>
      <button
        type="button"
        style={BTN}
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
      >Export CSV</button>
      <button type="button" style={BTN} onClick={clearFilters}>Clear Filters</button>
      <button type="button" style={BTN} onClick={reload}>Reload</button>
    </div>
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

      <div style={{ marginTop: '16px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          <p style={LABEL}>Delinquent: <strong>{summary.delinquentCount}</strong></p>
          <p style={LABEL}>Past Due: <strong>{formatCurrency(summary.delinquentBalance)}</strong></p>
          <p style={LABEL}>Credits: <strong>{formatCurrency(summary.credits)}</strong></p>
          <p style={LABEL}>Reversals: <strong>{summary.reversedCount}</strong></p>
        </div>
      </div>

      {selected ? (
        <Drawer onClose={() => setSelected(null)} width={500}>
          <div style={{ padding: '24px' }}>
            <h6 style={{ margin: 0, marginBottom: '1rem', fontWeight: 700, fontSize: '1.25rem' }}>Invoice Detail</h6>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <p style={LABEL}><strong>Payer:</strong> {selected.household_name}</p>
              <p style={LABEL}><strong>Total:</strong> {formatCurrency(selected.total_amount)}</p>
              <p style={LABEL}><strong>Paid:</strong> {formatCurrency(selected.paid_amount)}</p>
              <p style={LABEL}><strong>Balance:</strong> {formatCurrency(selected.balance_due)}</p>
              <p style={LABEL}><strong>Aging:</strong> {selected.aging_bucket}</p>
            </div>
            <div style={{ marginTop: '16px' }}>
              <button type="button" style={BTN} onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </CrownLayout>
  );
}

import { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  Typography,
} from '@mui/material';
import CrownTableToolbar from './CrownTableToolbar';
import { sortRows } from '../../utils/tableSort';

export default function CrownDataTable({
  title,
  subtitle,
  rows = [],
  columns = [],
  rowKey = 'id',
  loading = false,
  error = null,
  emptyTitle = 'No records found',
  emptyMessage = 'There is nothing to show here yet.',
  searchValue = '',
  onSearchChange,
  filters = null,
  actions = null,
  initialSortKey = '',
  initialSortDirection = 'asc',
  page = 0,
  rowsPerPage = 10,
  onPageChange,
  onRowsPerPageChange,
}) {
  const [sortKey, setSortKey] = useState(initialSortKey);
  const [sortDirection, setSortDirection] = useState(initialSortDirection);

  const sortedRows = useMemo(() => {
    return sortRows(rows, sortKey, sortDirection);
  }, [rows, sortKey, sortDirection]);

  const pagedRows = useMemo(() => {
    const start = page * rowsPerPage;
    return sortedRows.slice(start, start + rowsPerPage);
  }, [sortedRows, page, rowsPerPage]);

  const handleSort = (columnKey) => {
    if (sortKey === columnKey) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortKey(columnKey);
    setSortDirection('asc');
  };

  return (
    <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3 }}>
      <CrownTableToolbar
        title={title}
        subtitle={subtitle}
        searchValue={searchValue}
        onSearchChange={onSearchChange}
        filters={filters}
        actions={actions}
      />

      {loading ? (
        <Stack alignItems="center" spacing={1.5} sx={{ py: 6 }}>
          <CircularProgress />
          <Typography variant="body2">Loading table data...</Typography>
        </Stack>
      ) : error ? (
        <Alert severity="error">
          {typeof error === 'string' ? error : error?.message || 'Unable to load table data.'}
        </Alert>
      ) : !rows.length ? (
        <Box sx={{ py: 6 }}>
          <Typography variant="h6" fontWeight={700}>
            {emptyTitle}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {emptyMessage}
          </Typography>
        </Box>
      ) : (
        <>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {columns.map((column) => (
                    <TableCell
                      key={column.key}
                      sx={{ fontWeight: 700, whiteSpace: 'nowrap' }}
                    >
                      {column.sortable ? (
                        <TableSortLabel
                          active={sortKey === column.key}
                          direction={sortKey === column.key ? sortDirection : 'asc'}
                          onClick={() => handleSort(column.key)}
                        >
                          {column.label}
                        </TableSortLabel>
                      ) : (
                        column.label
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>

              <TableBody>
                {pagedRows.map((row, index) => (
                  <TableRow key={row?.[rowKey] ?? index} hover>
                    {columns.map((column) => (
                      <TableCell key={column.key}>
                        {typeof column.render === 'function'
                          ? column.render(row)
                          : row?.[column.key] ?? '—'}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={sortedRows.length}
            page={page}
            onPageChange={(_, nextPage) => onPageChange?.(nextPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(event) =>
              onRowsPerPageChange?.(Number(event.target.value))
            }
            rowsPerPageOptions={[10, 25, 50]}
          />
        </>
      )}
    </Paper>
  );
}

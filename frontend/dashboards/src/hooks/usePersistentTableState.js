import { useEffect, useMemo, useState } from 'react';
import { useUrlQueryState } from './useUrlQueryState';

export function usePersistentTableState(storageKey, defaults) {
  const { query, setQueryValues } = useUrlQueryState();

  const initialState = useMemo(() => {
    try {
      const raw = window.localStorage.getItem(`crown_table_state:${storageKey}`);
      const parsed = raw ? JSON.parse(raw) : {};
      return {
        ...defaults,
        ...parsed,
      };
    } catch {
      return defaults;
    }
  }, [storageKey, defaults]);

  const [search, setSearch] = useState(query.search ?? initialState.search ?? '');
  const [filters, setFilters] = useState(initialState.filters ?? {});
  const [page, setPage] = useState(Number(query.page ?? initialState.page ?? 0));
  const [rowsPerPage, setRowsPerPage] = useState(
    Number(query.rowsPerPage ?? initialState.rowsPerPage ?? 10),
  );

  useEffect(() => {
    const payload = {
      search,
      filters,
      page,
      rowsPerPage,
    };

    window.localStorage.setItem(
      `crown_table_state:${storageKey}`,
      JSON.stringify(payload),
    );
  }, [storageKey, search, filters, page, rowsPerPage]);

  useEffect(() => {
    const flatFilters = Object.entries(filters).reduce((acc, [key, value]) => {
      acc[`filter_${key}`] = value;
      return acc;
    }, {});

    setQueryValues({
      search,
      page,
      rowsPerPage,
      ...flatFilters,
    });
  }, [search, filters, page, rowsPerPage, setQueryValues]);

  const setFilter = (key, value) => {
    setPage(0);
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const clearFilters = () => {
    setPage(0);
    setSearch('');
    setFilters({});
  };

  return {
    search,
    setSearch: (value) => {
      setPage(0);
      setSearch(value);
    },
    filters,
    setFilter,
    clearFilters,
    page,
    setPage,
    rowsPerPage,
    setRowsPerPage: (value) => {
      setPage(0);
      setRowsPerPage(value);
    },
  };
}

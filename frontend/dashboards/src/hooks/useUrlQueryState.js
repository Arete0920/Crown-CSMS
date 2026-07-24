import { useMemo } from 'react';
import { useSearchParams } from 'react-router';
import { readQueryObject, writeQueryObject } from '../utils/queryState';

export function useUrlQueryState() {
  const [searchParams, setSearchParams] = useSearchParams();

  const query = useMemo(() => readQueryObject(searchParams), [searchParams]);

  const setQueryValue = (key, value) => {
    const next = writeQueryObject(searchParams, { [key]: value });
    setSearchParams(next, { replace: true });
  };

  const setQueryValues = (updates) => {
    const next = writeQueryObject(searchParams, updates);
    setSearchParams(next, { replace: true });
  };

  return {
    query,
    setQueryValue,
    setQueryValues,
  };
}

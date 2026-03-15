import { useCallback, useEffect, useState } from 'react';

export function useAsyncPageData(loader, deps = []) {
  void deps;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await loader();
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [loader]);

  useEffect(() => {
    run();
  }, [run]);

  return {
    loading,
    error,
    data,
    reload: run,
  };
}

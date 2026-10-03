import { useCallback, useEffect, useRef, useState } from 'react';

export function useAsyncPageData(loader, deps = []) {
  const loaderRef = useRef(loader);
  const generation = useRef(0);
  useEffect(() => { loaderRef.current = loader; });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = useCallback(async () => {
    const current = ++generation.current;
    setLoading(true);
    setError(null);

    try {
      const result = await loaderRef.current();
      if (current === generation.current) setData(result);
    } catch (err) {
      if (current === generation.current) setError(err);
    } finally {
      if (current === generation.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void run();
    return () => { generation.current += 1; };
    // The caller supplies a fixed-length dependency list, as with useEffect.
    // Loader identity is deliberately excluded: inline loaders change on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, ...deps]);

  return {
    loading,
    error,
    data,
    reload: run,
  };
}

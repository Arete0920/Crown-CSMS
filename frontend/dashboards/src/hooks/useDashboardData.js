import { useEffect, useMemo, useState } from 'react';
import { dashboardFetch } from '../api/dashboardClient';
import { DASHBOARD_DATA_REGISTRY } from '../config/dashboardDataRegistry';
import { DASHBOARD_CERTIFICATION_REGISTRY } from '../config/dashboardCertificationRegistry';

function isStrictModeEnabled() {
  return (
    typeof import.meta !== 'undefined' &&
    import.meta.env &&
    String(import.meta.env.VITE_DASHBOARD_STRICT_MODE).toLowerCase() === 'true'
  );
}

export default function useDashboardData(dashboardKey, options = {}) {
  const config = DASHBOARD_DATA_REGISTRY[dashboardKey];
  const certification =
    DASHBOARD_CERTIFICATION_REGISTRY[dashboardKey] || {
      status: 'scaffold',
      owner: 'Unknown',
      notes: '',
    };

  const [data, setData] = useState(config?.fallbackData ?? null);
  const [error, setError] = useState(
    config ? null : new Error(`No dashboard data config found for "${dashboardKey}".`)
  );
  const [loading, setLoading] = useState(Boolean(config) && (options.enabled ?? true));
  const [source, setSource] = useState(config?.fallbackData ? 'fallback' : 'none');
  const [lastLoadedAt, setLastLoadedAt] = useState(null);

  const effectiveOptions = useMemo(
    () => ({
      enabled: options.enabled ?? true,
      query: options.query,
    }),
    [options.enabled, options.query]
  );

  useEffect(() => {
    if (!effectiveOptions.enabled || !config) {
      return;
    }

    let isMounted = true;
    const strictMode = isStrictModeEnabled();

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const response = await dashboardFetch(config.endpoint, {
          method: config.method,
          query: {
            ...(config.query || {}),
            ...(effectiveOptions.query || {}),
          },
        });

        const transformed = config.transform ? config.transform(response) : response;

        if (!isMounted) return;

        setData(transformed);
        setSource('live');
        setLastLoadedAt(new Date().toISOString());
        setLoading(false);
      } catch (fetchError) {
        if (!isMounted) return;

        const canFallback =
          !strictMode &&
          config.allowScaffoldFallback &&
          config.fallbackData !== null &&
          config.fallbackData !== undefined;

        if (canFallback) {
          setData(config.fallbackData);
          setSource('fallback');
          setLastLoadedAt(new Date().toISOString());
          setError(fetchError);
          setLoading(false);
          return;
        }

        setError(fetchError);
        setSource('none');
        setLoading(false);
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [dashboardKey, config, effectiveOptions]);

  return {
    data,
    error,
    loading: effectiveOptions.enabled ? loading : false,
    source,
    lastLoadedAt,
    certification,
    config,
  };
}

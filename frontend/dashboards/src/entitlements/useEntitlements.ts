/**
 * useEntitlements.ts
 *
 * React hook that fetches the entitlement snapshot for the current tenant
 * from GET /api/v1/subscriptions/me/entitlements/ and memoises the result.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useEntitlements();
 *   if (data?.entitlements["admissions.pipeline"]?.enabled) { ... }
 */
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import type { EntitlementsSnapshot } from "./entitlements";

type UseEntitlementsResult = {
  data: EntitlementsSnapshot | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
};

export function useEntitlements(): UseEntitlementsResult {
  const [data, setData] = useState<EntitlementsSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiFetch("/api/v1/subscriptions/me/entitlements/")
      .then((json: EntitlementsSnapshot) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message || "Failed to load entitlements.");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [tick]);

  return { data, loading, error, refetch };
}

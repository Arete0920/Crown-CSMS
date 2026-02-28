/**
 * EntitlementGate.tsx
 *
 * Conditionally renders children based on whether a feature is enabled
 * for the current tenant.
 *
 * Usage:
 *   <EntitlementGate featureKey="admissions.pipeline">
 *     <AdmissionsPipelinePage />
 *   </EntitlementGate>
 *
 *   // With a fallback for disabled state:
 *   <EntitlementGate
 *     featureKey="analytics.advanced"
 *     fallback={<UpgradeBanner feature="Advanced Analytics" />}
 *   >
 *     <AdvancedAnalyticsDashboard />
 *   </EntitlementGate>
 *
 * While loading: renders null (no flash).
 * When feature disabled and no fallback: renders null.
 */
import React from "react";

import type { FeatureKey } from "./entitlements";
import { useEntitlements } from "./useEntitlements";

type EntitlementGateProps = {
  featureKey: FeatureKey | string;
  children: React.ReactNode;
  /** Rendered when feature is disabled (or subscription has no entry). */
  fallback?: React.ReactNode;
  /** Rendered while entitlements are loading. Defaults to null. */
  loadingNode?: React.ReactNode;
};

export function EntitlementGate({
  featureKey,
  children,
  fallback = null,
  loadingNode = null,
}: EntitlementGateProps): React.ReactElement | null {
  const { data, loading } = useEntitlements();

  if (loading) return <>{loadingNode}</> as React.ReactElement;

  const ent = data?.entitlements?.[featureKey];
  if (!ent?.enabled) return <>{fallback}</> as React.ReactElement;

  return <>{children}</> as React.ReactElement;
}

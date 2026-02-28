/**
 * entitlements.ts
 *
 * TypeScript contract for the Crown2026 entitlements system.
 *
 * Mirrors the shape returned by GET /api/v1/subscriptions/me/entitlements/
 */

export type Entitlement = {
  enabled: boolean;
  limit_int?: number | null;
  used_int?: number | null;
};

export type EntitlementsSnapshot = {
  plan_code: string;
  plan_name: string;
  is_trial: boolean;
  entitlements: Record<string, Entitlement>;
};

/**
 * Canonical feature key constants — prevents string typos across the codebase.
 * Mirror the keys registered in seed_plans.py.
 */
export const FEATURES = {
  IDENTITY_RBAC: "identity.rbac",
  ADMISSIONS_PIPELINE: "admissions.pipeline",
  BILLING_OBLIGATIONS: "billing.obligations",
  PAYMENTS_LEDGER: "payments.ledger",
  FINANCIAL_AID_AWARDS: "financial_aid.awards",
  COMMS_MESSAGING: "comms.messaging",
  COMMS_SMS: "comms.sms",
  DASHBOARDS_REPORTING: "dashboards.reporting",
  DASHBOARDS_BOARD: "dashboards.board",
  ACADEMICS_ATTENDANCE: "academics.attendance",
  ACADEMICS_GRADEBOOK: "academics.gradebook",
  ACADEMICS_SCHEDULING: "academics.scheduling",
  DISCIPLINE_INCIDENTS: "discipline.incidents",
  ACTIVITIES_EVENTS: "activities.events",
  INTEGRATIONS_PREMIUM: "integrations.premium",
  ANALYTICS_ADVANCED: "analytics.advanced",
  SOLOMON_KB: "solomon.kb",
} as const;

export type FeatureKey = (typeof FEATURES)[keyof typeof FEATURES];

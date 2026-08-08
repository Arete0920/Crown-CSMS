import type { Page, Request, Response } from "@playwright/test";

export type NetworkObservation = {
  url: string;
  status?: number;
  method?: string;
  failure?: string | null;
};

export type ProvenanceObservation = {
  url: string;
  method?: string;
  status?: number;
  value: string;
  source: "meta.served_from" | "meta.provenance" | "root.provenance";
};

export type MissingProvenanceObservation = {
  url: string;
  method?: string;
  status?: number;
};

export type NetworkRecorder = {
  observed: NetworkObservation[];
  failed: NetworkObservation[];
  nonLiveProvenance: ProvenanceObservation[];
  missingProvenance: MissingProvenanceObservation[];
  missingExpected: () => string[];
  finalize: () => Promise<void>;
};

export type NetworkRecorderOptions = {
  expectedApiFragments?: string[];
  provenanceRequiredApiFragments?: string[];
};

const LIVE_PROVENANCE_VALUES = new Set(["live", "live_db"]);
const DASHBOARD_SUMMARY_PATH = /^\/api\/v1\/dashboards\/[^/]+\/summary\/?$/;

function normalizeProvenanceValue(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.trim().toLowerCase();
  return normalized || null;
}

function classifyProvenanceValue(
  target: ProvenanceObservation[],
  row: NetworkObservation,
  value: unknown,
  source: ProvenanceObservation["source"],
): boolean {
  const normalized = normalizeProvenanceValue(value);
  if (!normalized) return false;
  if (!LIVE_PROVENANCE_VALUES.has(normalized)) {
    target.push({ url: row.url, method: row.method, status: row.status, value: normalized, source });
  }
  return true;
}

export function classifyProvenance(body: unknown): {
  hasProvenance: boolean;
  nonLiveValues: ProvenanceObservation[];
} {
  const nonLiveValues: ProvenanceObservation[] = [];
  if (!body || typeof body !== "object") return { hasProvenance: false, nonLiveValues };

  const root = body as Record<string, unknown>;
  const metaCandidate = root.meta;
  const meta = metaCandidate && typeof metaCandidate === "object"
    ? (metaCandidate as Record<string, unknown>)
    : null;
  const emptyRow: NetworkObservation = { url: "" };
  const explicitValues: Array<{ value: unknown; source: ProvenanceObservation["source"] }> = [];

  if (meta) {
    explicitValues.push(
      { value: meta.served_from, source: "meta.served_from" },
      { value: meta.provenance, source: "meta.provenance" },
    );
  }
  explicitValues.push({ value: root.provenance, source: "root.provenance" });

  let hasProvenance = false;
  for (const entry of explicitValues) {
    if (classifyProvenanceValue(nonLiveValues, emptyRow, entry.value, entry.source)) {
      hasProvenance = true;
    }
  }

  // `meta.source` is commonly a descriptive source/service identifier (for
  // example `dashboard_service` or `core_identity`), not a data-state value.
  // Preserve legacy fail-closed support for payloads that use `meta.source`
  // as their *only* provenance signal, but never let a descriptive source name
  // override an explicit served_from/provenance state.
  if (!hasProvenance && meta) {
    hasProvenance = classifyProvenanceValue(
      nonLiveValues,
      emptyRow,
      meta.source,
      "meta.source",
    );
  }

  return { hasProvenance, nonLiveValues };
}

function extractPathname(url: string): string {
  try {
    return new URL(url, "http://crown.local").pathname;
  } catch {
    return url.split(/[?#]/, 1)[0] ?? "";
  }
}

function stripSingleTrailingSlash(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith("/")) return pathname.slice(0, -1);
  return pathname;
}

export function isExpectedEndpoint(url: string, fragment: string): boolean {
  const actual = extractPathname(url).trim();
  const expected = extractPathname(fragment).trim();
  if (!actual || !expected) return false;

  if (DASHBOARD_SUMMARY_PATH.test(actual) || DASHBOARD_SUMMARY_PATH.test(expected)) {
    return actual === expected;
  }

  return stripSingleTrailingSlash(actual) === stripSingleTrailingSlash(expected);
}

export function isProvenanceDesignatedEndpoint(url: string, fragments: string[]): boolean {
  return fragments.some((fragment) => isExpectedEndpoint(url, fragment));
}

export function evaluateProvenanceRequirement(params: {
  url: string;
  method?: string;
  status?: number;
  body: unknown;
  provenanceRequiredApiFragments: string[];
}): { enforced: boolean; missing: boolean; nonLiveValues: ProvenanceObservation[] } {
  const { url, method, status, body, provenanceRequiredApiFragments } = params;
  const enforced = isProvenanceDesignatedEndpoint(url, provenanceRequiredApiFragments);
  if (!enforced) return { enforced: false, missing: false, nonLiveValues: [] };

  const classification = classifyProvenance(body);
  const nonLiveValues = classification.nonLiveValues.map((entry) => ({
    ...entry, url, method, status,
  }));
  return {
    enforced: true,
    missing: !classification.hasProvenance && (status ?? 0) < 400,
    nonLiveValues,
  };
}

export function shouldRecordMissingProvenanceForNonJson(params: {
  url: string;
  status?: number;
  contentType?: string;
  provenanceRequiredApiFragments: string[];
}): boolean {
  const { url, status, contentType = "", provenanceRequiredApiFragments } = params;
  return (
    (status ?? 0) < 400
    && !contentType.toLowerCase().includes("json")
    && isProvenanceDesignatedEndpoint(url, provenanceRequiredApiFragments)
  );
}

export function attachNetworkRecorder(
  page: Page,
  optionsOrExpectedFragments: NetworkRecorderOptions | string[] = [],
): NetworkRecorder {
  const options = Array.isArray(optionsOrExpectedFragments)
    ? { expectedApiFragments: optionsOrExpectedFragments, provenanceRequiredApiFragments: [] }
    : optionsOrExpectedFragments;
  const expectedApiFragments = options.expectedApiFragments ?? [];
  const provenanceRequiredApiFragments = options.provenanceRequiredApiFragments ?? [];
  const observed: NetworkObservation[] = [];
  const failed: NetworkObservation[] = [];
  const nonLiveProvenance: ProvenanceObservation[] = [];
  const missingProvenance: MissingProvenanceObservation[] = [];
  const pendingBodyInspections = new Set<Promise<void>>();

  const isApiOrExpected = (url: string): boolean => {
    const pathname = extractPathname(url);
    return pathname.startsWith("/api/")
      || expectedApiFragments.some((fragment) => isExpectedEndpoint(url, fragment));
  };

  page.on("response", (response: Response) => {
    const url = response.url();
    const status = response.status();
    if (!isApiOrExpected(url)) return;

    const row: NetworkObservation = { url, status, method: response.request().method() };
    observed.push(row);
    if (status >= 400) failed.push(row);

    const contentType = response.headers()["content-type"] || "";
    if (!contentType.toLowerCase().includes("json")) {
      if (shouldRecordMissingProvenanceForNonJson({
        url, status, contentType, provenanceRequiredApiFragments,
      })) {
        missingProvenance.push({ url, method: row.method, status: row.status });
      }
      return;
    }

    let inspectBody: Promise<void>;
    inspectBody = response.json()
      .then((body: unknown) => {
        const evaluation = evaluateProvenanceRequirement({
          url, method: row.method, status: row.status, body, provenanceRequiredApiFragments,
        });
        nonLiveProvenance.push(...evaluation.nonLiveValues);
        if (evaluation.missing) {
          missingProvenance.push({ url, method: row.method, status: row.status });
        }
      })
      .catch(() => {
        if (status < 400 && isProvenanceDesignatedEndpoint(url, provenanceRequiredApiFragments)) {
          missingProvenance.push({ url, method: row.method, status: row.status });
        }
      })
      .finally(() => pendingBodyInspections.delete(inspectBody));
    pendingBodyInspections.add(inspectBody);
  });

  page.on("requestfailed", (request: Request) => {
    const url = request.url();
    if (!isApiOrExpected(url)) return;
    failed.push({
      url,
      method: request.method(),
      failure: request.failure()?.errorText ?? "request failed",
    });
  });

  return {
    observed,
    failed,
    nonLiveProvenance,
    missingProvenance,
    missingExpected: () => {
      const seen = [...observed, ...failed];
      return expectedApiFragments.filter(
        (fragment) => !seen.some((row) => isExpectedEndpoint(row.url, fragment)),
      );
    },
    finalize: async () => {
      while (pendingBodyInspections.size > 0) {
        await Promise.allSettled([...pendingBodyInspections]);
      }
    },
  };
}

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
  source: "meta.served_from" | "meta.provenance" | "meta.source" | "root.provenance";
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

const NON_LIVE_PROVENANCE_VALUES = new Set(["snapshot", "sample", "fallback", "unknown"]);

function normalizeProvenanceValue(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = value.trim().toLowerCase();
  return normalized || null;
}

function recordIfNonLive(
  target: ProvenanceObservation[],
  row: NetworkObservation,
  value: unknown,
  source: ProvenanceObservation["source"],
): void {
  const normalized = normalizeProvenanceValue(value);
  if (!normalized || !NON_LIVE_PROVENANCE_VALUES.has(normalized)) {
    return;
  }

  target.push({
    url: row.url,
    method: row.method,
    status: row.status,
    value: normalized,
    source,
  });
}

export function classifyProvenance(body: unknown): {
  hasProvenance: boolean;
  nonLiveValues: ProvenanceObservation[];
} {
  const nonLiveValues: ProvenanceObservation[] = [];

  if (!body || typeof body !== "object") {
    return { hasProvenance: false, nonLiveValues };
  }

  const root = body as Record<string, unknown>;
  const metaCandidate = root.meta;
  const meta = metaCandidate && typeof metaCandidate === "object"
    ? (metaCandidate as Record<string, unknown>)
    : null;

  let hasProvenance = false;

  if (meta) {
    if (meta.served_from !== undefined) {
      hasProvenance = true;
    }
    if (meta.provenance !== undefined) {
      hasProvenance = true;
    }
    if (meta.source !== undefined) {
      hasProvenance = true;
    }

    recordIfNonLive(nonLiveValues, { url: "", method: undefined, status: undefined }, meta.served_from, "meta.served_from");
    recordIfNonLive(nonLiveValues, { url: "", method: undefined, status: undefined }, meta.provenance, "meta.provenance");
    recordIfNonLive(nonLiveValues, { url: "", method: undefined, status: undefined }, meta.source, "meta.source");
  }

  if (root.provenance !== undefined) {
    hasProvenance = true;
  }

  recordIfNonLive(nonLiveValues, { url: "", method: undefined, status: undefined }, root.provenance, "root.provenance");

  return { hasProvenance, nonLiveValues };
}

export function isProvenanceDesignatedEndpoint(url: string, fragments: string[]): boolean {
  return fragments.some((fragment) => url.includes(fragment));
}

export function evaluateProvenanceRequirement(params: {
  url: string;
  method?: string;
  status?: number;
  body: unknown;
  provenanceRequiredApiFragments: string[];
}): {
  enforced: boolean;
  missing: boolean;
  nonLiveValues: ProvenanceObservation[];
} {
  const {
    url,
    method,
    status,
    body,
    provenanceRequiredApiFragments,
  } = params;

  const enforced = isProvenanceDesignatedEndpoint(url, provenanceRequiredApiFragments);
  if (!enforced) {
    return { enforced: false, missing: false, nonLiveValues: [] };
  }

  const classification = classifyProvenance(body);
  const nonLiveValues = classification.nonLiveValues.map((entry) => ({
    ...entry,
    url,
    method,
    status,
  }));

  return {
    enforced: true,
    missing: !classification.hasProvenance && (status ?? 0) < 400,
    nonLiveValues,
  };
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
  const pendingBodyInspections: Array<Promise<void>> = [];

  page.on("response", (response: Response) => {
    const url = response.url();
    const status = response.status();
    const isApi = url.includes("/api/") || expectedApiFragments.some((fragment) => url.includes(fragment));

    if (!isApi) {
      return;
    }

    const row = {
      url,
      status,
      method: response.request().method(),
    };

    observed.push(row);

    if (status >= 400) {
      failed.push(row);
    }

    const contentType = response.headers()["content-type"] || "";
    if (!contentType.toLowerCase().includes("application/json")) {
      return;
    }

    const inspectBody = response.json()
      .then((body: unknown) => {
        const evaluation = evaluateProvenanceRequirement({
          url,
          method: row.method,
          status: row.status,
          body,
          provenanceRequiredApiFragments,
        });

        for (const nonLiveValue of evaluation.nonLiveValues) {
          nonLiveProvenance.push({
            ...nonLiveValue,
            url,
            method: row.method,
            status: row.status,
          });
        }

        if (evaluation.missing) {
          missingProvenance.push({
            url,
            method: row.method,
            status: row.status,
          });
        }
      })
      .catch(() => {
        // Not all API responses are JSON objects with provenance metadata.
      });

    pendingBodyInspections.push(inspectBody);
  });

  page.on("requestfailed", (request: Request) => {
    const url = request.url();
    const isApi = url.includes("/api/") || expectedApiFragments.some((fragment) => url.includes(fragment));

    if (!isApi) {
      return;
    }

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
        (fragment) => !seen.some((row) => row.url.includes(fragment)),
      );
    },
    finalize: async () => {
      await Promise.allSettled(pendingBodyInspections);
    },
  };
}

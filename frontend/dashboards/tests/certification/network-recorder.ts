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

export type NetworkRecorder = {
  observed: NetworkObservation[];
  failed: NetworkObservation[];
  nonLiveProvenance: ProvenanceObservation[];
  missingExpected: () => string[];
  finalize: () => Promise<void>;
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

export function attachNetworkRecorder(page: Page, expectedApiFragments: string[] = []): NetworkRecorder {
  const observed: NetworkObservation[] = [];
  const failed: NetworkObservation[] = [];
  const nonLiveProvenance: ProvenanceObservation[] = [];
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
        if (!body || typeof body !== "object") {
          return;
        }

        const root = body as Record<string, unknown>;
        const metaCandidate = root.meta;
        const meta = metaCandidate && typeof metaCandidate === "object"
          ? (metaCandidate as Record<string, unknown>)
          : null;

        if (meta) {
          recordIfNonLive(nonLiveProvenance, row, meta.served_from, "meta.served_from");
          recordIfNonLive(nonLiveProvenance, row, meta.provenance, "meta.provenance");
          recordIfNonLive(nonLiveProvenance, row, meta.source, "meta.source");
        }

        recordIfNonLive(nonLiveProvenance, row, root.provenance, "root.provenance");
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

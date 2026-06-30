import type { Page, Request, Response } from "@playwright/test";

export type NetworkObservation = {
  url: string;
  status?: number;
  method?: string;
  failure?: string | null;
};

export type NetworkRecorder = {
  observed: NetworkObservation[];
  failed: NetworkObservation[];
  missingExpected: () => string[];
};

export function attachNetworkRecorder(page: Page, expectedApiFragments: string[] = []): NetworkRecorder {
  const observed: NetworkObservation[] = [];
  const failed: NetworkObservation[] = [];

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
    missingExpected: () => {
      const seen = [...observed, ...failed];
      return expectedApiFragments.filter(
        (fragment) => !seen.some((row) => row.url.includes(fragment)),
      );
    },
  };
}

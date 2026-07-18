import fs from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext } from "@playwright/test";

type SafePayload = {
  code?: string;
  detail?: string;
  servedFrom?: string;
  provenance?: string;
};

type ProbeObservation = {
  name: string;
  path: string;
  status: number;
  ok: boolean;
  sentTenantHeader: boolean;
  sentAuthentication: boolean;
  payload: SafePayload;
};

const API_BASE = requireUrl("CROWN_LIVE_API_BASE_URL");
const SCHOOL_ID = (
  process.env.CROWN_DEMO_SCHOOL_ID
  || process.env.CROWN_LIVE_SCHOOL_ID
  || "19801b59-8c05-4c84-9312-5d792e4e839d"
).trim();
const INVITE_ID = (process.env.CROWN_LIVE_SANDBOX_INVITE_ID || "").trim();
const SUMMARY_PATH = "/api/v1/dashboards/school-administrator/summary";
const SESSION_PATH = "/api/v1/sandbox/session/";
const evidenceRoot = path.resolve(
  process.cwd(),
  "../../audit-artifacts/tenant-context/current",
);

function requireUrl(name: string): string {
  const raw = process.env[name]?.trim();
  if (!raw) throw new Error(`${name} is required for live tenant-context proof.`);
  const parsed = new URL(raw);
  if (["localhost", "127.0.0.1", "0.0.0.0"].includes(parsed.hostname)) {
    throw new Error(`${name} must target a deployed runtime.`);
  }
  return parsed.toString().replace(/\/+$/, "");
}

function safePayload(value: unknown): SafePayload {
  if (!value || typeof value !== "object") return {};
  const root = value as Record<string, unknown>;
  const meta = root.meta && typeof root.meta === "object"
    ? root.meta as Record<string, unknown>
    : {};
  return {
    code: typeof root.code === "string" ? root.code : undefined,
    detail: typeof root.detail === "string" ? root.detail : undefined,
    servedFrom: typeof meta.served_from === "string" ? meta.served_from : undefined,
    provenance: typeof meta.provenance === "string" ? meta.provenance : undefined,
  };
}

async function readJson(response: Awaited<ReturnType<APIRequestContext["get"]>>): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function getAccessToken(request: APIRequestContext): Promise<string> {
  const payload: Record<string, string> = {
    role: "school_admin",
    school: "heritage",
    guidance: "guided",
    track: "school",
  };
  if (INVITE_ID) payload.invite_id = INVITE_ID;

  const response = await request.post(`${API_BASE}${SESSION_PATH}`, { data: payload });
  const body = await readJson(response);
  const access = body && typeof body === "object"
    ? (body as Record<string, unknown>).access
    : undefined;
  if (!response.ok() || typeof access !== "string" || !access) {
    throw new Error(
      `Sandbox session bootstrap failed: status=${response.status()} code=${safePayload(body).code || "unknown"}. `
      + "Configure CROWN_LIVE_SANDBOX_INVITE_ID when the deployed runtime requires an invite.",
    );
  }
  return access;
}

async function probe(
  request: APIRequestContext,
  name: string,
  headers: Record<string, string>,
): Promise<ProbeObservation> {
  const response = await request.get(`${API_BASE}${SUMMARY_PATH}`, { headers });
  const body = await readJson(response);
  return {
    name,
    path: SUMMARY_PATH,
    status: response.status(),
    ok: response.ok(),
    sentTenantHeader: Boolean(headers["X-School-Id"]),
    sentAuthentication: Boolean(headers.Authorization),
    payload: safePayload(body),
  };
}

function writeEvidence(rows: ProbeObservation[]): void {
  fs.mkdirSync(evidenceRoot, { recursive: true });
  fs.writeFileSync(
    path.join(evidenceRoot, "tenant-context-runtime-proof.json"),
    `${JSON.stringify({ schoolId: SCHOOL_ID, observations: rows }, null, 2)}\n`,
    "utf8",
  );
}

test.describe.configure({ mode: "serial", retries: 0 });

test("dashboard tenant context is fail-closed and succeeds with trusted context", async ({ request }) => {
  const accessToken = await getAccessToken(request);
  const rows = [
    await probe(request, "no-context", {}),
    await probe(request, "tenant-header", { "X-School-Id": SCHOOL_ID }),
    await probe(request, "authenticated-session", { Authorization: `Bearer ${accessToken}` }),
    await probe(request, "authenticated-plus-header", {
      Authorization: `Bearer ${accessToken}`,
      "X-School-Id": SCHOOL_ID,
    }),
  ];
  writeEvidence(rows);

  const noContext = rows[0];
  expect(noContext.status).toBe(400);
  expect(noContext.payload.code).toBe("missing_tenant");

  const trustedContextRows = rows.slice(1);
  const successful = trustedContextRows.filter((row) => row.ok);
  expect(
    successful.length,
    `No trusted-context probe succeeded: ${JSON.stringify(trustedContextRows)}`,
  ).toBeGreaterThan(0);

  const authenticated = rows[2];
  const authenticatedPlusHeader = rows[3];
  expect(
    authenticated.ok || authenticatedPlusHeader.ok,
    `Authenticated dashboard summary failed: ${JSON.stringify([authenticated, authenticatedPlusHeader])}`,
  ).toBe(true);
});

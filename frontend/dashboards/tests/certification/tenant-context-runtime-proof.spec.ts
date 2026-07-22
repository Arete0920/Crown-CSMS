import fs from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext } from "@playwright/test";

type SafePayload = {
  code?: string;
  detail?: string;
  servedFrom?: string;
  provenance?: string;
};

type LiveIdentity = {
  id: string;
  expectedRoles: string[];
  email: string;
  password: string;
};

type IdentityObservation = {
  id: string;
  expectedRoles: string[];
  authenticatedEmail?: string;
  authenticatedRole?: string;
  authenticatedSchoolId?: string;
  tokenStatus: number;
  meStatus: number;
  whoamiStatus: number;
  whoamiBuildSha?: string;
  resolvedTenantSchoolId?: string;
  dashboardStatus: number;
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
const SCHOOL_ID = requireValue("CROWN_LIVE_SCHOOL_ID");
const EXPECTED_API_SHA = requireValue("CROWN_EXPECTED_API_SHA").toLowerCase();
const SUMMARY_PATH = "/api/v1/dashboards/school-administrator/summary";
const TOKEN_PATH = "/api/v1/auth/token/";
const ME_PATH = "/api/auth/me/";
const WHOAMI_PATH = "/api/system/whoami/";
const evidenceRoot = path.resolve(process.cwd(), "../../audit-artifacts/tenant-context/current");

const identities: LiveIdentity[] = [
  identity("admin", ["admin", "school_admin", "head_of_school"]),
  identity("teacher", ["teacher"]),
  identity("parent", ["parent"]),
  identity("student", ["student"]),
  identity("board", ["board", "head_of_school"]),
];

function requireUrl(name: string): string {
  const raw = requireValue(name);
  const parsed = new URL(raw);
  if (["localhost", "127.0.0.1", "0.0.0.0"].includes(parsed.hostname)) {
    throw new Error(`${name} must target a deployed runtime.`);
  }
  return parsed.toString().replace(/\/+$/, "");
}

function requireValue(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required for live tenant-context proof.`);
  return value;
}

function identity(id: string, expectedRoles: string[]): LiveIdentity {
  const prefix = `CROWN_LIVE_${id.toUpperCase()}`;
  return {
    id,
    expectedRoles,
    email: requireValue(`${prefix}_EMAIL`),
    password: requireValue(`${prefix}_PASSWORD`),
  };
}

function safePayload(value: unknown): SafePayload {
  if (!value || typeof value !== "object") return {};
  const root = value as Record<string, unknown>;
  const meta = root.meta && typeof root.meta === "object" ? root.meta as Record<string, unknown> : {};
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

async function authenticate(request: APIRequestContext, identityRecord: LiveIdentity): Promise<{ access: string; status: number }> {
  const response = await request.post(`${API_BASE}${TOKEN_PATH}`, {
    data: { username: identityRecord.email, password: identityRecord.password },
    headers: { "X-School-Id": SCHOOL_ID },
  });
  const body = await readJson(response);
  const access = body && typeof body === "object" ? (body as Record<string, unknown>).access : undefined;
  expect(response.status(), `${identityRecord.id} token request failed`).toBe(200);
  expect(typeof access, `${identityRecord.id} token response missing access`).toBe("string");
  expect(String(access).length, `${identityRecord.id} token was empty`).toBeGreaterThan(0);
  return { access: String(access), status: response.status() };
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

function writeEvidence(identityRows: IdentityObservation[], tenantRows: ProbeObservation[]): void {
  fs.mkdirSync(evidenceRoot, { recursive: true });
  fs.writeFileSync(
    path.join(evidenceRoot, "tenant-context-runtime-proof.json"),
    `${JSON.stringify({
      expectedApiSha: EXPECTED_API_SHA,
      schoolId: SCHOOL_ID,
      identities: identityRows,
      observations: tenantRows,
    }, null, 2)}\n`,
    "utf8",
  );
}

test.describe.configure({ mode: "serial", retries: 0 });

test("five live identities, roles, tenant binding, build identity, and fail-closed context are verified", async ({ request }) => {
  expect(SCHOOL_ID).toMatch(/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/);
  expect(EXPECTED_API_SHA).toMatch(/^[0-9a-f]{40}$/);

  const distinctEmails = new Set(identities.map((entry) => entry.email.trim().toLowerCase()));
  expect(distinctEmails.size, "Five distinct live accounts are required").toBe(identities.length);

  const identityRows: IdentityObservation[] = [];
  let adminAccess = "";

  for (const identityRecord of identities) {
    const token = await authenticate(request, identityRecord);
    if (identityRecord.id === "admin") adminAccess = token.access;
    const headers = {
      Authorization: `Bearer ${token.access}`,
      "X-School-Id": SCHOOL_ID,
    };

    const meResponse = await request.get(`${API_BASE}${ME_PATH}`, { headers });
    const meBody = await readJson(meResponse) as Record<string, any>;
    const meUser = meBody?.user ?? {};
    expect(meResponse.status(), `${identityRecord.id} /api/auth/me/ failed`).toBe(200);
    expect(String(meUser.email || "").toLowerCase()).toBe(identityRecord.email.toLowerCase());
    expect(identityRecord.expectedRoles).toContain(String(meUser.role || "").toLowerCase());
    expect(String(meUser.school_id || "").toLowerCase()).toBe(SCHOOL_ID.toLowerCase());

    const whoamiResponse = await request.get(`${API_BASE}${WHOAMI_PATH}`, { headers });
    const whoamiBody = await readJson(whoamiResponse) as Record<string, any>;
    expect(whoamiResponse.status(), `${identityRecord.id} whoami failed`).toBe(200);
    expect(String(whoamiBody?.user?.email || "").toLowerCase()).toBe(identityRecord.email.toLowerCase());
    expect(identityRecord.expectedRoles).toContain(String(whoamiBody?.user?.role || "").toLowerCase());
    expect(String(whoamiBody?.tenant?.resolved_school_id || "").toLowerCase()).toBe(SCHOOL_ID.toLowerCase());
    expect(String(whoamiBody?.build?.build_sha || "").toLowerCase()).toBe(EXPECTED_API_SHA);

    const dashboardResponse = await request.get(`${API_BASE}${SUMMARY_PATH}`, { headers });
    expect(
      dashboardResponse.status(),
      `${identityRecord.id} authenticated dashboard request returned an unexpected server error`,
    ).toBeLessThan(500);

    identityRows.push({
      id: identityRecord.id,
      expectedRoles: identityRecord.expectedRoles,
      authenticatedEmail: meUser.email,
      authenticatedRole: meUser.role,
      authenticatedSchoolId: meUser.school_id,
      tokenStatus: token.status,
      meStatus: meResponse.status(),
      whoamiStatus: whoamiResponse.status(),
      whoamiBuildSha: whoamiBody?.build?.build_sha,
      resolvedTenantSchoolId: whoamiBody?.tenant?.resolved_school_id,
      dashboardStatus: dashboardResponse.status(),
    });
  }

  expect(adminAccess, "Administrator access token was not captured").not.toBe("");
  const tenantRows = [
    await probe(request, "no-context", {}),
    await probe(request, "tenant-header", { "X-School-Id": SCHOOL_ID }),
    await probe(request, "authenticated-session", { Authorization: `Bearer ${adminAccess}` }),
    await probe(request, "authenticated-plus-header", {
      Authorization: `Bearer ${adminAccess}`,
      "X-School-Id": SCHOOL_ID,
    }),
  ];
  writeEvidence(identityRows, tenantRows);

  expect(tenantRows[0].status).toBe(400);
  expect(tenantRows[0].payload.code).toBe("missing_tenant");
  expect(
    tenantRows[2].ok || tenantRows[3].ok,
    `Authenticated administrator dashboard summary failed: ${JSON.stringify([tenantRows[2], tenantRows[3]])}`,
  ).toBe(true);
});

import fs from "node:fs";
import { test, expect } from "@playwright/test";

// Keep short-lived fixture credentials out of trace artifacts.
test.use({ trace: "off", video: "off" });

const api = process.env.CROWN_LIVE_API_BASE_URL;
if (api !== "https://crown-api-dev.azurewebsites.net") throw new Error("This synthetic fixture proof is DEV only");
const fixturePath = process.env.CROWN_DEV_TENANT_FIXTURE;
if (!fixturePath) throw new Error("CROWN_DEV_TENANT_FIXTURE required");
const schools = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
if (schools.length !== 2 || schools[0].school_id === schools[1].school_id) throw new Error("Two distinct synthetic schools required");

for (const school of schools) {
  const foreign = schools.find((other) => other.school_id !== school.school_id);
  for (const [role, actor] of Object.entries(school.actors) as [string, { token: string }][]) {
    test(`${school.school_id} / ${role}: real navigation and cross-school denials`, async ({ request }) => {
      const headers = { Authorization: `Bearer ${actor.token}`, "X-School-Id": school.school_id };
      const own = await request.get(`${api}/api/v1/nav/`, { headers });
      expect(own.status()).toBe(200);
      const cross = await request.get(`${api}/api/v1/nav/`, { headers: { ...headers, "X-School-Id": foreign.school_id } });
      expect(cross.status()).toBe(404);
      expect((await cross.json()).code).toBe("tenant_access_denied");
      const object = await request.get(`${api}/api/students/${foreign.student_id}/`, { headers });
      expect(object.status()).toBe(404);
    });
  }
  test(`${school.school_id}: saved synthetic student survives independent reads`, async ({ request }) => {
    const headers = { Authorization: `Bearer ${school.actors.school_admin.token}`, "X-School-Id": school.school_id };
    for (let read = 0; read < 2; read++) {
      const response = await request.get(`${api}/api/students/${school.student_id}/`, { headers });
      expect(response.status()).toBe(200);
      const saved = await response.json();
      expect(saved.id).toBe(school.student_id);
      expect(saved.first_name).toBe("Synthetic");
    }
  });
}


test('Heritage Board renewal preserves least privilege and tenant isolation', async ({ playwright }) => {
  // A separate context prevents cookies from another persona masking authorization.
  const context = await playwright.request.newContext();
  try {
    const healthResponse = await context.get(`${api}/api/health/`);
    expect(healthResponse.status()).toBe(200);
    const health = await healthResponse.json();
    expect(health.env).toBe('dev');
    expect(health.build_sha).toBe(health.artifact_build_sha);
    expect(health.db).toBe('ok');
    let schoolId: string | undefined;
    const sessions: { access: string; school_id: string }[] = [];
    for (let renewal = 0; renewal < 2; renewal++) {
      const issuer = await playwright.request.newContext();
      let session;
      try {
        const response = await issuer.post(`${api}/api/v1/sandbox/session/`, {
          data: { role: 'board', school: 'heritage-core', track: 'school' },
        });
        expect(response.status(), 'authorized Heritage Board session').toBe(201);
        session = await response.json();
      } finally {
        await issuer.dispose();
      }
      expect(session.role_code).toBe('board_member');
      expect(session.role).toBe('board');
      expect(typeof session.access === 'string' && session.access.length > 0).toBe(true);
      if (schoolId) expect(session.school_id).toBe(schoolId);
      schoolId = session.school_id;
      sessions.push({ access: session.access, school_id: session.school_id });
    }
    // Exercise both issued tokens after renewal, then repeat independent reads.
    for (const session of sessions) {
      const headers = { Authorization: `Bearer ${session.access}`, 'X-School-Id': session.school_id };
      for (let read = 0; read < 2; read++) {
        const navigation = await context.get(`${api}/api/v1/nav/`, { headers });
        expect(navigation.status()).toBe(200);
        const menu = await navigation.json();
        const links = menu.groups.flatMap((group: { items: { href: string }[] }) => group.items.map(item => item.href));
        expect(links).toContain('/board');
        for (const forbidden of ['/admin', '/finance', '/billing']) expect(links).not.toContain(forbidden);
        const board = await context.get(`${api}/api/v1/academics/classroom/workspace/?audience=board`, { headers });
        expect(board.status()).toBe(200);
        const aggregate = await board.json();
        for (const key of ['students', 'assignments', 'lesson_plans', 'categories', 'sections']) {
          expect(Object.hasOwn(aggregate, key)).toBe(false);
        }
        const signals = await context.get(`${api}/api/signals/board/risk-counts/`, { headers });
        expect(signals.status()).toBe(200);
        for (const route of [
          '/api/v1/academics/classroom/workspace/?audience=admin',
          '/api/v1/admin/metrics/',
          '/api/v1/finance/metrics/',
          '/api/v1/sandbox/admin/state/',
          '/api/v1/sandbox/finance/state/',
        ]) {
          const denied = await context.get(`${api}${route}`, { headers });
          expect(denied.status(), route).toBe(403);
        }
        for (const foreign of schools) {
          for (const route of [
            '/api/signals/board/risk-counts/',
            '/api/v1/nav/',
            '/api/v1/academics/classroom/workspace/?audience=board',
          ]) {
            const cross = await context.get(`${api}${route}`, {
              headers: { ...headers, 'X-School-Id': foreign.school_id },
            });
            expect(cross.status(), route).toBe(404);
            expect((await cross.json()).code).toBe('tenant_access_denied');
          }
        }
      }
    }
  } finally {
    await context.dispose();
  }
});

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

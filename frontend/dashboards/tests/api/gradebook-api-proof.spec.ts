import { test, expect } from "@playwright/test";

const BASE_URL = process.env.CROWN_UI_URL ?? "http://localhost:3000";
const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const USERNAME = "head@crown-demo.local";
const PASSWORD = "demo1234";
const SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962";

test("Gradebook Proof: Roster + Grades + Assignments with 200s + auth headers", async ({ page }) => {
  // Step 1: Get an auth token via the UI
  console.log("[Auth] Logging in to get bearer token...");
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);

  // The DevJwtPanel now uses single-button login (no input fields)
  // Capture the login response before clicking
  const loginResponsePromise = page.waitForResponse((r) => {
    const url = r.url();
    return r.request().method() === "POST" && url.includes("/api/") && url.includes("token");
  });

  // Click "Demo Login" button (single-button deterministic auth)
  await page.getByRole("button", { name: /Demo Login/i }).click();

  // Wait for the backend response
  const loginResp = await loginResponsePromise;
  console.log("[Auth] loginResp status:", loginResp.status());
  console.log("[Auth] loginResp url:", loginResp.url());

  // Extract token from response JSON (try multiple common key names)
  let authToken: string | null = null;
  try {
    const data: any = await loginResp.json();
    authToken = data?.access ?? data?.token ?? data?.jwt ?? null;
    if (authToken) {
      console.log("[Auth] Token extracted from JSON response");
    }
  } catch (err) {
    console.log("[Auth] Could not parse JSON response:", err);
  }

  // If not in JSON, try cookies (common for httpOnly JWT setups)
  if (!authToken) {
    const cookies = await page.context().cookies();
    console.log("[Auth] Cookies:", cookies.map((c) => c.name).join(", "));

    const accessCookie =
      cookies.find((c) => /access/i.test(c.name)) ??
      cookies.find((c) => /jwt/i.test(c.name)) ??
      cookies.find((c) => /token/i.test(c.name));

    authToken = accessCookie?.value ?? null;
    if (authToken) {
      console.log("[Auth] Token extracted from cookies");
    }
  }

  // Fall back to sessionStorage if all else fails (the original approach)
  if (!authToken) {
    const storedToken = await page.evaluate(() => {
      return sessionStorage.getItem("crown.jwt.access");
    });
    authToken = storedToken;
    if (authToken) {
      console.log("[Auth] Token extracted from sessionStorage (legacy)");
    }
  }

  // Validate token exists before proceeding
  expect(authToken, "Token not found in login response, cookies, or sessionStorage").toBeTruthy();
  console.log("TOKEN_OK=true");

  // Extract school ID from sessionStorage (this one works reliably)
  const schoolId = await page.evaluate(() => sessionStorage.getItem("crown.school.id"));
  expect(schoolId, "School ID not found in sessionStorage after login").toBeTruthy();
  console.log("SCHOOL_ID_OK=true\n");

  // Fetch first available section (resilient to seed variability)
  console.log("[Setup] Fetching available sections from API...");
  const sectionsResp = await page.request.get(`${API_BASE}/api/v1/academics/sections/`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      "X-School-Id": SCHOOL_ID,
    },
  });
  expect(sectionsResp.status(), "Sections API should return 200").toBe(200);
  const sectionsData: any = await sectionsResp.json();
  const sections = sectionsData?.results ?? sectionsData?.data ?? sectionsData ?? [];
  expect(sections.length, "At least one section must exist for proof").toBeGreaterThan(0);
  const SECTION_ID = sections[0].section_id;
  console.log(`[Setup] Using section: ${SECTION_ID}\n`);

  // Step 2: Use the captured token to directly verify the three endpoints
  // (Direct API calls because UI navigation doesn't easily expose all three endpoint triggers)
  console.log(`\n[API Proof] Testing three endpoints with captured token...`);

  const endpoints = [
    {
      name: "Roster",
      url: `${API_BASE}/api/v1/academics/sections/${SECTION_ID}/roster/`,
      pattern: /roster/i,
    },
    {
      name: "Grades",
      url: `${API_BASE}/api/v1/gradebook/sections/${SECTION_ID}/grades/`,
      pattern: /grades/i,
    },
    {
      name: "Assignments",
      url: `${API_BASE}/api/v1/gradebook/sections/${SECTION_ID}/assignments/`,
      pattern: /assignments/i,
    },
  ];

  const results: Array<{ name: string; status: number; pass: boolean }> = [];

  for (const endpoint of endpoints) {
    const response = await page.request.get(endpoint.url, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        "X-School-Id": SCHOOL_ID,
      },
    });

    const status = response.status();
    const pass = status === 200;

    results.push({
      name: endpoint.name,
      status,
      pass,
    });

    console.log(`  ${endpoint.name}: ${status} ${pass ? "✅" : "❌"}`);
  }

  // Step 3: Take screenshots to document the UI state
  console.log(`\n[UI] Navigating to Academics for roster screenshot...`);
  await page.goto(`${BASE_URL}/academics`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "gb-ui-section-roster.png", fullPage: true });
  console.log(`  Saved gb-ui-section-roster.png`);

  console.log(`[UI] Navigating to Gradebook for grades grid screenshot...`);
  await page.goto(`${BASE_URL}/gradebook`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "gb-ui-gradebook-grid.png", fullPage: true });
  console.log(`  Saved gb-ui-gradebook-grid.png`);

  // Step 4: Validate results
  console.log(`\n[Results Summary]`);
  results.forEach((r) => {
    console.log(`  ${r.name}: HTTP ${r.status} ${r.pass ? "✅ PASS" : "❌ FAIL"}`);
  });

  const allPass = results.every((r) => r.pass && r.status === 200);

  expect(results[0].pass, `Roster endpoint returned ${results[0].status}, expected 200`).toBe(true);
  expect(results[1].pass, `Grades endpoint returned ${results[1].status}, expected 200`).toBe(true);
  expect(results[2].pass, `Assignments endpoint returned ${results[2].status}, expected 200`).toBe(true);

  // Validate that requests were sent with required headers
  // (HTTP 200 response proves the backend accepted the Authorization + X-School-Id headers)
  console.log(`\n[Headers Proof]`);
  console.log(`  Each request was sent with:`);
  console.log(`    - Authorization: Bearer [token]`);
  console.log(`    - X-School-Id: ${SCHOOL_ID}`);
  console.log(`  All 200 responses prove headers were accepted by backend. ✅`);

  console.log(`\n✅ PASS: All three endpoints returned 200 with required auth headers.`);
});

/**
 * Real Chromium route interactions with deliberately intercepted fictional APIs.
 * This is UI state-machine evidence, NOT a live Django custody/audit proof.
 * Never present the synthetic response store as backend persistence.
 * Producer integration for "crown:auth-context-changed" belongs to PR #612.
 */
import { expect, test, type Page, type Route } from "@playwright/test";

const SCHOOL_A = "11111111-1111-4111-8111-111111111111";
const SCHOOL_B = "22222222-2222-4222-8222-222222222222";
const CHILD_A = "33333333-3333-4333-8333-333333333333";
const CHILD_B = "44444444-4444-4444-8444-444444444444";
const AM = "/before-care/roster";
const PM = "/aftercare/roster";
const NAV = { groups: [] };

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

function careRoster(school: string, session: string, attendance: Record<string, unknown> | null = null) {
  const isForeign = school === SCHOOL_B;
  const rows = session === "AM" || isForeign ? [{
    student_id: isForeign ? CHILD_B : CHILD_A,
    student_name: isForeign ? "Fictional Child B" : "Fictional Child A",
    care_session: session,
    enrollment: { billing_model: "FLAT_MONTHLY" },
    attendance,
    unscheduled: false,
  }] : [];
  return { date: "2026-11-03", dow: "TUE", care_session: session, rows, unlinked_attendance_count: 0 };
}

async function setupStaff(page: Page) {
  await page.addInitScript(({school}) => {
    sessionStorage.setItem("crown.jwt.access", "fictional-care-staff-A-token");
    sessionStorage.setItem("crown.school.id", school);
    sessionStorage.setItem("crown.role", "aftercare_staff");
    sessionStorage.setItem("crown.active.role", "aftercare_staff");
  }, { school: SCHOOL_A });
  await page.route("**/api/v1/nav/**", route => json(route, NAV));
}

async function changeSchool(page: Page, school: string) {
  await page.evaluate((id) => {
    sessionStorage.setItem("crown.school.id", id);
    window.dispatchEvent(new Event("crown:school-context-changed"));
  }, school);
}

async function spaNavigate(page: Page, pathname: string) {
  await page.evaluate((next) => {
    window.history.pushState(null, "", next);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, pathname);
  await expect(page).toHaveURL(new RegExp(pathname.replace(/\//g, "\\/") + "$"));
}

test.describe("Extended Care fictional custody browser isolation (mocked API)", () => {
  test("AM pending check-in survives PM route and foreign-school switch; only originating verified readback resolves", async ({ page }) => {
    await setupStaff(page);
    let checkins = 0;
    let committed = false;
    let releaseWrite: (() => Promise<void>) | undefined;
    const postSchools: string[] = [];

    await page.route("**/api/v1/aftercare/**", async route => {
      const request = route.request();
      const url = new URL(request.url());
      const school = request.headers()["x-school-id"] || "";
      const session = url.searchParams.get("care_session") || "PM";
      if (url.pathname.endsWith("/roster/today/") && request.method() === "GET") {
        if (school !== SCHOOL_A && school !== SCHOOL_B) return json(route, { detail: "Unknown fictional school" }, 403);
        return json(route, careRoster(school, session,
          school === SCHOOL_A && committed
            ? { checkin_time: "2026-11-03T08:05:00Z", checkout_time: null } : null));
      }
      if (url.pathname.endsWith("/attendance/checkin/") && request.method() === "POST") {
        checkins += 1;
        postSchools.push(school);
        await new Promise<void>(resolve => {
          releaseWrite = async () => {
            committed = true;
            await json(route, { id: 17, care_session: "AM" }, 201);
            resolve();
          };
        });
        return;
      }
      return json(route, { detail: "Unexpected fictional custody request" }, 403);
    });

    await page.goto(AM, { waitUntil: "domcontentloaded" });
    await expect(page.getByText("Fictional Child A")).toBeVisible();
    await page.getByRole("button", { name: "Check In" }).click();
    await expect.poll(() => checkins).toBe(1);
    await spaNavigate(page, PM);
    await expect(page.getByText(/outcome is unconfirmed/i)).toBeVisible();
    await expect(page.getByRole("button", { name: "Review current custody before continuing" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Check In" })).toHaveCount(0);

    await changeSchool(page, SCHOOL_B);
    await expect(page.getByText("Fictional Child B")).toBeVisible();
    await expect(page.getByText("Fictional Child A")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Review current custody before continuing" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Check In" })).toHaveCount(0);
    expect(postSchools).toEqual([SCHOOL_A]);

    expect(releaseWrite, "pending fictional POST must be interceptable").toBeDefined();
    await releaseWrite!();
    await expect(page.getByText(/previous custody write is still pending/i)).toHaveCount(0);
    await expect(page.getByText(/outcome is unconfirmed/i)).toBeVisible();
    await changeSchool(page, SCHOOL_A);
    await spaNavigate(page, AM);
    await expect(page.getByRole("button", { name: "Review current custody before continuing" })).toBeEnabled();
    await expect(page.getByRole("button", { name: "Check In" })).toHaveCount(0);
    await page.getByRole("button", { name: "Review current custody before continuing" }).click();
    await expect(page.getByText(/outcome is unconfirmed/i)).toHaveCount(0);
    await expect(page.getByText("Checked in", { exact: true })).toBeVisible();
    expect(checkins, "readback must not replay a custody write").toBe(1);
  });

  test("PM ambiguous pickup cannot replay until the matching row proves verified transfer", async ({ page }) => {
    await setupStaff(page);
    let checkoutCalls = 0;
    let stage: "open" | "unverified" | "verified" = "open";
    const checkedIn = { checkin_time: "2026-11-03T15:05:00Z", checkout_time: null };

    await page.route("**/api/v1/aftercare/**", async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      const school = request.headers()["x-school-id"];
      if (school !== SCHOOL_A) return json(route, { detail: "Wrong school" }, 403);
      if (path.endsWith("/roster/today/")) {
        const attendance = stage === "open" ? checkedIn
          : { ...checkedIn, checkout_time: "2026-11-03T17:05:00Z", pickup_verified: stage === "verified" };
        return json(route, {
          date: "2026-11-03", dow: "TUE", care_session: "PM",
          rows: [{ student_id: CHILD_A, student_name: "Fictional Child A", care_session: "PM",
            enrollment: { billing_model: "FLAT_MONTHLY" }, attendance, unscheduled: false }],
          unlinked_attendance_count: 0,
        });
      }
      if (path.endsWith("/pickup-contacts/")) {
        return json(route, [{ id: 7, name: "Fictional Guardian A", is_active: true }]);
      }
      if (path.endsWith("/attendance/checkout/")) {
        checkoutCalls += 1;
        stage = "unverified";
        return json(route, { detail: "Fictional ambiguous response" }, 504);
      }
      return json(route, { detail: "Unexpected request" }, 403);
    });

    await page.goto(PM, { waitUntil: "domcontentloaded" });
    await expect(page.getByText("Fictional Child A")).toBeVisible();
    await page.getByRole("button", { name: "Verify Pickup" }).click();
    await page.getByRole("combobox", { name: "Authorized pickup contact" }).click();
    await page.getByRole("option", { name: /Fictional Guardian A/ }).click();
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: "Confirm Checkout" }).click();
    await expect(page.getByText(/outcome is unconfirmed/i)).toBeVisible();
    await expect(page.getByRole("dialog", { name: /Verify Authorized Pickup/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Verify Pickup" })).toHaveCount(0);
    await page.getByRole("button", { name: "Review current custody before continuing" }).click();
    await expect(page.getByText(/roster does not confirm the original custody transition/i)).toBeVisible();
    await expect(page.getByText(/outcome is unconfirmed/i)).toBeVisible();

    stage = "verified";
    await page.getByRole("button", { name: "Review current custody before continuing" }).click();
    await expect(page.getByText(/outcome is unconfirmed/i)).toHaveCount(0);
    await expect(page.getByText("Checked out", { exact: true })).toBeVisible();
    expect(checkoutCalls).toBe(1);
  });

  test("same-tab staff replacement event immediately removes old child's actions without focus", async ({ page }) => {
    await setupStaff(page);
    await page.route("**/api/v1/aftercare/**", route => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith("/roster/today/")) return json(route, careRoster(SCHOOL_A, "AM"));
      return json(route, { detail: "Not available" }, 403);
    });
    await page.goto(AM, { waitUntil: "domcontentloaded" });
    await expect(page.getByText("Fictional Child A")).toBeVisible();
    await page.evaluate(() => {
      sessionStorage.setItem("crown.jwt.access", "fictional-care-staff-B-token");
      // Consumer-only proof. PR #612 must install the actual event producer.
      window.dispatchEvent(new Event("crown:auth-context-changed"));
    });
    await expect(page.getByText("Fictional Child A")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Check In" })).toHaveCount(0);
  });
});

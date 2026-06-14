import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const routeRegistryPath = path.resolve(process.cwd(), "src/routes/wizards.js");
const pagesRoot = path.resolve(process.cwd(), "src/pages");

const lateWizardRoutes = [
  { path: "/student-import-setup", component: "StudentImportWizard" },
  { path: "/guardian-household-setup", component: "SetupWizardA" },
  { path: "/section-staffing-setup", component: "SetupWizardC" },
  { path: "/attendance-codes-setup", component: "AttendanceSetupWizard" },
  { path: "/grade-weights-setup", component: "CategoriesWizard" },
];

test.describe("Wizard UI completion contract", () => {
  test("late wizard routes use dedicated components, not WizardHub", () => {
    const source = fs.readFileSync(routeRegistryPath, "utf8");

    for (const route of lateWizardRoutes) {
      expect(source).toContain(`path: '${route.path}'`);
      expect(source).toContain(`component: ${route.component}`);
    }

    for (const route of lateWizardRoutes) {
      const routeIndex = source.indexOf(`path: '${route.path}'`);
      const nextRouteIndex = source.indexOf("{ path:", routeIndex + 1);
      const block = source.slice(routeIndex, nextRouteIndex > routeIndex ? nextRouteIndex : source.length);
      expect(block).not.toContain("component: WizardHub");
    }
  });

  test("late wizard component files are implemented workflow pages", () => {
    for (const route of lateWizardRoutes) {
      const filePath = path.join(pagesRoot, `${route.component}.jsx`);
      const source = fs.readFileSync(filePath, "utf8");
      expect(source).toContain("apiFetch");
      expect(source).toContain("commit");
      expect(source).toContain("verify");
      expect(source).not.toContain("return null");
    }
  });
});

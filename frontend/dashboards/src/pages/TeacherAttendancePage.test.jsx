import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import TeacherAttendancePage from "./TeacherAttendancePage";
import { authenticatedFetch } from "../utils/authClient";

vi.mock("../utils/authClient", () => ({ authenticatedFetch: vi.fn() }));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));

const TODAY = new Date().toISOString().slice(0, 10);
const SECTIONS = [
  { section_id: "section-a", course_name: "English" },
  { section_id: "section-b", course_name: "Science" },
];
const ROSTERS = {
  "section-a": [{ student_id: "student-a", name: "Caleb Demo" }],
  "section-b": [{ student_id: "student-b", name: "Naomi Demo" }],
};
let saved;
let reads;
let writes;

function response(payload) {
  return { json: async () => structuredClone(payload) };
}

function attendance(sectionId, overrides = {}) {
  return {
    source: "live",
    section_id: sectionId,
    date: TODAY,
    roster: ROSTERS[sectionId].map((student) => ({
      id: student.student_id,
      identity_verified: true,
      attendance: saved[sectionId]?.[student.student_id] ?? null,
    })),
    ...overrides,
  };
}

async function selectSection(sectionId = "section-a") {
  await screen.findByRole("option", { name: "English" });
  fireEvent.change(screen.getByLabelText("Section:"), { target: { value: sectionId } });
}

function statusControl() {
  return screen.getAllByRole("combobox")[1];
}

beforeEach(() => {
  saved = {};
  reads = {};
  writes = [];
  authenticatedFetch.mockImplementation(async (path, options = {}) => {
    if (path === "/api/v1/academics/sections/") return response({ results: SECTIONS });
    if (path === "/api/v1/academics/classroom/operations/") {
      const sectionId = options.query.section_id;
      expect(options.query.date).toBe(TODAY);
      return reads[sectionId] ? reads[sectionId]() : response(attendance(sectionId));
    }
    const match = path.match(/^\/api\/v1\/academics\/sections\/([^/]+)\/(roster|attendance)\/$/);
    if (!match) throw new Error(`Unexpected request: ${path}`);
    const [, sectionId, action] = match;
    if (action === "roster") return response({ students: ROSTERS[sectionId] });
    expect(options.method).toBe("POST");
    const payload = JSON.parse(options.body);
    writes.push({ sectionId, ...payload });
    saved[sectionId] = Object.fromEntries(payload.items.map((item) => [item.student_id, item.status.toUpperCase()]));
    return response({ created: 1, updated: 0, date: payload.date });
  });
});

afterEach(() => { cleanup(); vi.resetAllMocks(); });

it("restores saved attendance after the page is recreated", async () => {
  const first = render(<TeacherAttendancePage />);
  await selectSection();
  await screen.findByText("Caleb Demo");
  expect(statusControl().value).toBe("present");
  fireEvent.change(statusControl(), { target: { value: "absent" } });
  fireEvent.click(screen.getByRole("button", { name: "Submit Attendance" }));
  await screen.findByText(/Saved: created=1/);
  expect(writes).toEqual([{ sectionId: "section-a", date: TODAY, items: [{ student_id: "student-a", status: "absent" }] }]);
  first.unmount();

  render(<TeacherAttendancePage />);
  await selectSection();
  await screen.findByText("Caleb Demo");
  expect(statusControl().value).toBe("absent");
  expect(writes).toHaveLength(1);
});

it("preserves canonical excused marks and keeps unsaved edits local", async () => {
  saved["section-a"] = { "student-a": "EXCUSED" };
  render(<TeacherAttendancePage />);
  await selectSection();
  await screen.findByText("Caleb Demo");
  expect(statusControl().value).toBe("excused");
  fireEvent.change(statusControl(), { target: { value: "tardy" } });
  expect(statusControl().value).toBe("tardy");
  expect(saved["section-a"]["student-a"]).toBe("EXCUSED");
  expect(writes).toEqual([]);
  fireEvent.click(screen.getByRole("button", { name: "Submit Attendance" }));
  await screen.findByText(/Saved: created=1/);
  expect(writes[0].items).toEqual([{ student_id: "student-a", status: "tardy" }]);
});

it.each([
  ["unavailable", () => { throw new Error("HTTP 403"); }],
  ["wrong section", () => response(attendance("section-a", { section_id: "section-b" }))],
  ["wrong date", () => response(attendance("section-a", { date: "2000-01-01" }))],
  ["missing roster member", () => response(attendance("section-a", { roster: [] }))],
  ["unverified identity", () => response(attendance("section-a", { roster: [{ id: "student-a", identity_verified: false, attendance: null }] }))],
  ["invalid status", () => response(attendance("section-a", { roster: [{ id: "student-a", identity_verified: true, attendance: "UNKNOWN" }] }))],
])("keeps writes disabled when saved attendance is %s", async (_label, read) => {
  reads["section-a"] = read;
  render(<TeacherAttendancePage />);
  await selectSection();
  await screen.findByRole("alert");
  expect(screen.getByRole("button", { name: "Submit Attendance" }).disabled).toBe(true);
  expect(screen.queryByText("Caleb Demo")).toBeNull();
  expect(writes).toEqual([]);
});

it("ignores an older section response while waiting for the current section", async () => {
  let finishA;
  let finishB;
  reads["section-a"] = () => new Promise((resolve) => { finishA = resolve; });
  reads["section-b"] = () => new Promise((resolve) => { finishB = resolve; });
  render(<TeacherAttendancePage />);
  await selectSection("section-a");
  await waitFor(() => expect(finishA).toBeTypeOf("function"));
  expect(screen.getByRole("button", { name: "Submit Attendance" }).disabled).toBe(true);
  await selectSection("section-b");
  await waitFor(() => expect(finishB).toBeTypeOf("function"));
  await act(async () => finishA(response(attendance("section-a"))));
  expect(screen.queryByText("Caleb Demo")).toBeNull();
  expect(screen.getByRole("button", { name: "Submit Attendance" }).disabled).toBe(true);
  saved["section-b"] = { "student-b": "TARDY" };
  await act(async () => finishB(response(attendance("section-b"))));
  await screen.findByText("Naomi Demo");
  expect(statusControl().value).toBe("tardy");
  expect(screen.getByRole("button", { name: "Submit Attendance" }).disabled).toBe(false);
  expect(writes).toEqual([]);
});

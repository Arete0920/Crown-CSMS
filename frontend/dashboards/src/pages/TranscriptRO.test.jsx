// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { TranscriptRO } from "./TranscriptRO.jsx";
import { fetchStudents, fetchTranscript } from "../api/academics";
import { downloadOfficialTranscriptPdf, issueOfficialTranscript } from "../api/transcript";

vi.mock("../api/academics", () => ({
  fetchStudents: vi.fn(),
  fetchTranscript: vi.fn(),
}));
vi.mock("../api/transcript", () => ({
  issueOfficialTranscript: vi.fn(),
  downloadOfficialTranscriptPdf: vi.fn(),
}));
vi.mock("../auth/roleAdapter", () => ({
  getCurrentUserRoles: () => ["registrar"],
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));

const students = [
  { id: "student-a", first_name: "Alpha", last_name: "One", grade_level: "8" },
  { id: "student-b", first_name: "Beta", last_name: "Two", grade_level: "9" },
];
const documentFor = (id) => ({
  student: { student_id: id, first_name: id === "student-a" ? "Alpha" : "Beta",
    last_name: id === "student-a" ? "One" : "Two", grade_level: "8" },
  terms: [], cumulative_gpa: null, attempted_credits: 0, earned_credits: 0,
});
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};

beforeEach(() => { vi.resetAllMocks(); });
afterEach(cleanup);

it.each([
  ["actual DRF array", students],
  ["future paginated response", { results: students }],
])("loads transcript students from %s", async (_label, roster) => {
  fetchStudents.mockResolvedValue(roster);
  fetchTranscript.mockImplementation(async (id) => documentFor(id));
  render(<TranscriptRO />);
  expect(await screen.findByText("Academic Transcript")).toBeTruthy();
  expect(screen.getByRole("combobox", { name: "Student" }).options).toHaveLength(2);
  expect(fetchTranscript).toHaveBeenCalledWith("student-a");
});

it("fails closed on malformed student roster instead of showing a false empty state", async () => {
  fetchStudents.mockResolvedValue({ items: students });
  render(<TranscriptRO />);
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Invalid students response"));
  expect(fetchTranscript).not.toHaveBeenCalled();
});

it("prevents an older transcript response from replacing the newly selected student's record", async () => {
  const old = deferred();
  const latest = deferred();
  fetchStudents.mockResolvedValue(students);
  fetchTranscript.mockImplementation((id) => id === "student-a" ? old.promise : latest.promise);
  render(<TranscriptRO />);
  await waitFor(() => expect(fetchTranscript).toHaveBeenCalledWith("student-a"));
  fireEvent.change(screen.getByRole("combobox", { name: "Student" }), { target: { value: "student-b" } });
  await waitFor(() => expect(fetchTranscript).toHaveBeenCalledWith("student-b"));
  expect(screen.getByRole("button", { name: "Issue Official PDF" }).disabled).toBe(true);
  latest.resolve(documentFor("student-b"));
  expect(await screen.findByText("Two, Beta")).toBeTruthy();
  old.resolve(documentFor("student-a"));
  await waitFor(() => expect(screen.getByText("Two, Beta")).toBeTruthy());
  expect(screen.queryByText("One, Alpha")).toBeNull();
  expect(screen.getByRole("button", { name: "Issue Official PDF" }).disabled).toBe(false);
});

it("rejects a cross-student transcript identity and cannot issue it", async () => {
  fetchStudents.mockResolvedValue(students);
  fetchTranscript.mockResolvedValue(documentFor("student-b"));
  render(<TranscriptRO />);
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("identity does not match selection"));
  expect(screen.queryByText("Two, Beta")).toBeNull();
  expect(screen.getByRole("button", { name: "Issue Official PDF" }).disabled).toBe(true);
});


it("does not download or attribute an in-flight official issuance to the next student", async () => {
  const pendingIssuance = deferred();
  fetchStudents.mockResolvedValue(students);
  fetchTranscript.mockImplementation(async (id) => documentFor(id));
  issueOfficialTranscript.mockReturnValue(pendingIssuance.promise);
  downloadOfficialTranscriptPdf.mockResolvedValue(new Blob(["%PDF-1.4"]));
  render(<TranscriptRO />);
  await screen.findByText("One, Alpha");
  fireEvent.click(screen.getByRole("button", { name: "Issue Official PDF" }));
  await waitFor(() => expect(issueOfficialTranscript).toHaveBeenCalledWith("student-a"));
  fireEvent.change(screen.getByRole("combobox", { name: "Student" }), {
    target: { value: "student-b" },
  });
  await screen.findByText("Two, Beta");
  await act(async () => {
    pendingIssuance.resolve({ issuance_id: "synthetic-issuance", artifact_sha256: "a".repeat(64) });
    await pendingIssuance.promise;
  });
  expect(downloadOfficialTranscriptPdf).not.toHaveBeenCalled();
  expect(screen.queryByRole("status")).toBeNull();
  expect(screen.getByText("Two, Beta")).toBeTruthy();
});

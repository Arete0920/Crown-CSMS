import { describe, expect, it } from "vitest";
import { buildClassroomKpis } from "../pages/classroomKpis.js";

const asValues = (input) => Object.fromEntries(
  buildClassroomKpis(input).map((row) => [row.label, row.value]),
);

describe("live classroom KPI evidence", () => {
  it("does not show fictional metrics when the school has no classrooms", () => {
    expect(asValues({ classrooms: [], loading: false, error: "" })).toEqual({
      "Active classrooms": "0",
      "Roster entries": "0",
      "Homerooms staffed": "0",
    });
  });

  it("counts authorized classroom records, roster memberships and staffed rooms", () => {
    expect(asValues({
      classrooms: [
        { id: "a", student_count: 12, homeroom_teacher_name: "Taylor Sample" },
        { id: "b", student_count: 18, homeroom_teacher_name: "" },
        { id: "c", student_count: 0, homeroom_teacher_name: "Jordan Sample" },
      ],
      loading: false,
      error: "",
    })).toEqual({
      "Active classrooms": "3",
      "Roster entries": "30",
      "Homerooms staffed": "2",
    });
  });

  it("never presents unavailable API data as actual zero counts", () => {
    for (const input of [
      { classrooms: [], loading: true, error: "" },
      { classrooms: [{ student_count: 12 }], loading: false, error: "Access denied" },
      { classrooms: null, loading: false, error: "" },
    ]) {
      expect(Object.values(asValues(input))).toEqual(["—", "—", "—"]);
    }
  });

  it("does not invent roster counts if a server response omits student_count", () => {
    const values = asValues({
      classrooms: [
        { id: "a", student_count: 8, homeroom_teacher_name: "Teacher A" },
        { id: "b", homeroom_teacher_name: "" },
      ],
      loading: false,
      error: "",
    });
    expect(values["Active classrooms"]).toBe("2");
    expect(values["Roster entries"]).toBe("—");
    expect(values["Homerooms staffed"]).toBe("1");
  });

  it("uses truthful names and distinguishes memberships from unique children", () => {
    const cards = buildClassroomKpis({ classrooms: [], loading: false, error: "" });
    expect(cards.map((x) => x.label)).not.toContain("Announcements");
    expect(cards.find((x) => x.label === "Roster entries").definition).toContain("memberships");
    expect(cards.every((x) => x.dataSource === "Classroom list API")).toBe(true);
  });
});

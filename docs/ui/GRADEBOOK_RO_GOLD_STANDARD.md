# GradebookRO: Gold Standard Grid Pattern

**Purpose:** GradebookRO is the reference implementation for read-only data grids in Crown2026. This document freezes the patterns for consistent cloning across modules.

---

## Non-Negotiables

### Sticky Positioning
- Sticky is applied to `<th>` / `<td>` elements, **never** to `<tr>`
- Opaque `background` on all sticky cells (prevents ghosting)
- Three z-index layers: header/corner > sticky sides > body

### Derived Values
- All computed totals, averages, sorting use `useMemo()`
- Memos depend on their source arrays + sort state
- Memoized results are injected directly into render loops

### Empty States
- Explicit JSX blocks, not null checks
- Include title + message + optional action
- One per condition (no sections, no assignments, no students)

### Export
- CSV respects current sorted row/column order
- Uses shared helper: `csvEscape()` + `downloadTextFile()`
- Filename includes section name: `gradebook_{section}.csv`
- Button: top-right above table, flexbox-aligned

---

## Patterns

### Layout & Structure
```jsx
{!loadingGrades && hasAssignments && hasRows && (
  <>
    <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginBottom: 10 }}>
      <button onClick={onExportCsv}>Export CSV ↓</button>
    </div>
    <div style={{ overflowX: "auto" }}>
      <table>...</table>
    </div>
  </>
)}
```
- Export bar above table, flex-right aligned
- Fragment wraps both (export + overflow container)
- Table has `borderCollapse: "collapse"`, `minWidth: 900`

### Sticky Header (Two-Row Pattern)
**Row 1:** Titles (top: 0)
- Student: sticky left + sort buttons (Name, Avg)
- Assignments: sticky top
- Total: sticky right + top

**Row 2:** Averages (top: HEADER_ROW_HEIGHT)
- Blank sticky left cell + column sort buttons (Title, Avg)
- Assignment averages: sticky top
- Blank sticky right

**Why two rows:**
- Visual hierarchy (titles + stats)
- Sort controls separated by context (row vs. column)

### Sticky Columns
**Left (Student):**
- Always opaque white background
- z-index: 11 (left in row 1), 11 (left in row 2)
- No minimum width; content-fit

**Right (Total):**
- Always opaque white background
- z-index: 12 (right in row 1), lighter in row 2
- `whiteSpace: "nowrap"` to prevent text wrap

**Corner (Row 1, left):**
- Highest z-index (11), opaque
- Contains sort buttons for rows

### Sorting
**State:**
```jsx
const [rowSort, setRowSort] = useState({ key: "name", dir: "asc" });
const [colSort, setColSort] = useState({ key: "title", dir: "asc" });
```

**Memos:**
- `sortedRows`: depends on `rowSort` + `totalsByStudentId`
- `sortedAssignments`: depends on `colSort` + `assignmentAverages`
- Both return new sorted array; no mutation

**Render loops:**
- All assignment renders use `sortedAssignments.map()`
- All student row renders use `sortedRows.map()`
- No unsorted loops in grid render area

**Buttons:**
- Row sort: "Name" (default) + "Avg" (by total %)
- Column sort: "Title" (default) + "Avg" (by class average)
- Toggle logic: same key → flip direction; new key → reset to default

### Totals & Averages
**Per-student totals (memoized):**
```jsx
const totalsByStudentId = useMemo(() => {
  const map = new Map();
  for (const r of rows) {
    const sid = r.student.student_id || `${r.student.first_name}-${r.student.last_name}`;
    map.set(sid, calcRowTotals(r, assignments));
  }
  return map;
}, [rows, assignments]);
```

**Per-assignment averages (memoized):**
```jsx
const assignmentAverages = useMemo(() => {
  const map = new Map();
  for (const a of assignments) {
    const key = a._key ?? a.id;
    // compute earned/possible across all students
    map.set(key, { earned, possible, pct, n });
  }
  return map;
}, [rows, assignments]);
```

**Key consistency rule:** Assignment keys must match between:
- `a._key` used in render loops
- Score lookup `r._scores?.[a._key]`
- Average lookup `assignmentAverages.get(key)`

Use stable key: `a._key = keyOf(a.assignment_name)` (trimmed name).

### CSV Export
**Helper signature:**
```jsx
csvEscape(value) → string (escapes quotes, handles newlines)
downloadTextFile(filename, text) → void (blob + anchor download)
buildGradebookCsv() → string (CSV with headers, respects sorted view)
onExportCsv() → void (handler; calls buildGradebookCsv + download)
```

**CSV content:**
- Header: Student, [Assignment names], Total Earned, Total Possible, Total %
- Rows: student name, [grade cells], totals
- Uses `sortedRows` + `sortedAssignments` (current sort order honored)
- Cells: `${pts}/${max} (${pct}%)` or blank if missing

### Color Cues (Optional)
**Helper:**
```jsx
pctFromCell(cell) → pct or null (safe percent from earned/possible)
bgForPct(pct) → color string or undefined
  ≥ 90: rgba(34, 197, 94, 0.10)  // green
  70–89: rgba(234, 179, 8, 0.12)   // amber
  < 70: rgba(239, 68, 68, 0.10)   // red
```

**Apply to:**
- Grade cells: `background: bgForPct(pctFromCell(cell))`
- Total cell: `background: bgForPct(totals?.pct) ?? "#fff"`

**Why optional:** Adds context without being loud. Students can grok performance at a glance.

---

## Proof Loop Checklist

Before committing any B4 slice:

- [ ] `npm run build` succeeds (no TypeScript errors)
- [ ] Manual smoke test:
  - [ ] Name sort (rows flip A→Z then Z→A)
  - [ ] Avg sort (rows flip by total % high→low then low→high)
  - [ ] Title sort (columns flip alphabetically)
  - [ ] Avg sort columns (columns flip by class average)
- [ ] Sticky headers stay pinned while scrolling
- [ ] Sticky left/right columns stay pinned while scrolling horizontally
- [ ] No cells "go blank" after sorting (key consistency verified)
- [ ] Export CSV downloads
- [ ] CSV content matches current visible sorted order
- [ ] `git show --stat HEAD` shows exact files changed

---

## Implementation Checklist (B4 Slicing)

- [ ] **B4.A** — Sticky total/average column per student
- [ ] **B4.B** — Assignment class averages row
- [ ] **B4.C** — Client-side sorting (rows + columns)
- [ ] **B4.D** — Subtle grade-range color cues
- [ ] **B4.E** — CSV export respecting current sort

All five should run in a single PR (or be merged before cloning to next module).

---

## Cloning to Next Module

When starting a new grid (Admissions Pipeline, Finance invoices, etc.):

1. Reference this doc
2. Copy exact structure: export bar + two-row sticky header + sorting state
3. Use shared helpers: `csvEscape`, `downloadTextFile`, z-index constants, color helpers
4. Ensure key stability (trim whitespace, use consistent ID contracts)
5. Run proof loop before merging
6. Update this doc if you discover a missing pattern

---

**Last Updated:** 2026-02-04
**Status:** Frozen / Reference
**Associated Code:** `frontend/dashboards/src/pages/GradebookRO.jsx`

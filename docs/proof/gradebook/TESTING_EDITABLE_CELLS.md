# Editable Grade Cells - Testing Guide

## Status: ✅ **Implementation Complete**

Frontend editable grade cells have been successfully implemented. Backend PATCH endpoint tested and verified.

---

## What Was Implemented

### Frontend Changes ([GradebookGrid.jsx](frontend/dashboards/src/pages/GradebookGrid.jsx))

1. **Added State Management:**
   ```jsx
   const [pendingUpdates, setPendingUpdates] = useState({});
   ```

2. **Added Helper Function:**
   ```jsx
   const findGradeEntry = (studentId, assignmentName) => {
     const row = data.rows.find(r => r.student.student_id === studentId);
     if (!row) return null;
     return row.scores?.[assignmentName] || null;
   };
   ```

3. **Added Change Handler:**
   ```jsx
   const handleScoreChange = (studentId, assignmentName, value) => {
     setPendingUpdates(prev => ({
       ...prev,
       [`${studentId}_${assignmentName}`]: value
     }));
   };
   ```

4. **Added Save Handler (PATCH Call):**
   ```jsx
   const handleScoreSave = async (studentId, assignmentName) => {
     const key = `${studentId}_${assignmentName}`;
     const newValue = pendingUpdates[key];
     if (newValue === undefined) return;
     
     const entry = findGradeEntry(studentId, assignmentName);
     if (!entry?.grade_entry_id) return;
     
     await fetch(`/api/v1/gradebook/grade-entries/${entry.grade_entry_id}/`, {
       method: "PATCH",
       headers: {
         "Content-Type": "application/json",
         "Authorization": `Bearer ${localStorage.getItem("access")}`,
         "X-School-Id": sessionStorage.getItem("crown.school.id"),
       },
       body: JSON.stringify({ points_earned: parseFloat(newValue) }),
     });
     
     fetchGradebook();
   };
   ```

5. **Replaced Score Cell with Input:**
   - Changed from: `<span>{score.points_earned}</span>`
   - Changed to: `<input type="number" step="0.01" value={...} onChange={...} onBlur={...} />`

### Backend Already Complete
- ✅ PATCH endpoint: `/api/v1/gradebook/grade-entries/{entry_id}/`
- ✅ Tenant-scoped (X-School-Id header enforced)
- ✅ Auth-required (JWT Bearer token)
- ✅ Field-restricted (only points_earned changeable)
- ✅ grade_entry_id included in grades response
- ✅ Tested with curl: 200 status, DB mutation confirmed

---

## Testing Instructions

### Prerequisites
- Django server running: `http://127.0.0.1:8000`
- Vite dev server running: `http://localhost:3000`
- User logged in (JWT token in localStorage)
- X-School-Id in sessionStorage

### Test Flow

1. **Navigate to Academics Page:**
   - URL: `http://localhost:3000/academics`
   - Should see sections with roster counts (e.g., "4 students")

2. **Click Roster Link:**
   - Click any section with students
   - Should navigate to: `/gradebook/{section_id}`

3. **Verify Gradebook Display:**
   - Should show section metadata (course, term, section ID)
   - Should show assignment columns (Homework 1, Quiz 1-4, etc.)
   - Should show student rows with real names (Ava Brooks, Ben Brooks, etc.)
   - Should show calculated percentages (88.5%, 88.3%, 70.1%, 60.5%)
   - **NEW:** Grade cells should now be editable input fields

4. **Edit a Grade:**
   - Click into any score cell
   - Current value should be highlighted
   - Change the value (e.g., 8.5 → 9.2)
   - Click out of the cell (blur event)

5. **Verify Save/Refresh Cycle:**
   - **Check Network Tab:** Should see PATCH request to `/api/v1/gradebook/grade-entries/{id}/`
   - **Check Status:** Should be 200 OK
   - **Check Response:** Should show updated points_earned
   - **Check UI:** Grid should automatically refresh (fetchGradebook() called)
   - **Check Percent Column:** Should recalculate (e.g., 88.5% → 89.3%)

6. **Verify Persistence:**
   - Hard refresh page (Ctrl+Shift+R)
   - Edited value should persist
   - Percent calculation should reflect new value

---

## Expected Test Section

**Section ID:** `8edf9a61-5f4f-4ec4-b33b-4447db22d9de`

- Course: Math/Biology (varies)
- Term: Fall 2024 or similar
- School: Heritage Christian Academy
- Student Count: 4 students
- Assignment Count: ~5 assignments (Homework 1, Quizzes)

---

## Verification Checklist

- [ ] Frontend compiles without errors
- [ ] Django server running
- [ ] Can navigate from Academics to Gradebook
- [ ] Gradebook displays with input fields (not spans)
- [ ] Can click into cell and edit value
- [ ] On blur, PATCH request fires
- [ ] Network request shows 200 status
- [ ] Grid refreshes automatically
- [ ] Percent column recalculates
- [ ] Hard refresh shows persisted value

---

## Known Constraints (By Design)

- **Field restriction:** Only `points_earned` is editable (cannot change student, assignment, school)
- **Tenant scoping:** Must have X-School-Id header (enforced server-side)
- **Auth requirement:** Must have valid JWT token in localStorage
- **No validation UI yet:** Invalid inputs (negative, > points_possible) are sent to server but no error UI shown
- **No loading states:** No spinner or disabled state during PATCH

---

## Next Steps (Polish - Not MVP Blockers)

- Add loading state during save (disable input, show spinner)
- Add error UI if PATCH fails (red border, toast notification)
- Add client-side validation (0 <= value <= points_possible)
- Add "unsaved changes" indicator (yellow border for edited cells)
- Add keyboard shortcuts (Enter to save, Esc to cancel)
- Add timestamps ("Last edited 2 minutes ago")

---

## Commit History

1. `dd956d7e` - Backend: Add PATCH endpoint for grade updates
2. `00d0dd34` - Backend: Include grade_entry_id in grades response
3. `7e35f23b` - Backend: Fix gradebook/ prefix in route
4. Current commit - Frontend: Add editable cells with blur-to-save

# GRADES PAYLOAD DOCUMENTATION (from backend code)

## GET /api/v1/gradebook/sections/<section_id>/grades/

**Response Shape (from gradebook/views.py lines 118-173):**

```json
{
  "section_id": "uuid-string",
  "assignments": [
    {
      "assignment_name": "Quiz 1",
      "points_possible": "10.00"
    },
    {
      "assignment_name": "Homework 1",
      "points_possible": "20.00"
    }
  ],
  "rows": [
    {
      "student": {
        "student_id": "uuid-string",
        "first_name": "Jane",
        "last_name": "Smith",
        "grade_level": "9"
      },
      "scores": {
        "Quiz 1": {
          "points_earned": "9.00",
          "points_possible": "10.00"
        },
        "Homework 1": {
          "points_earned": "18.50",
          "points_possible": "20.00"
        }
      }
    }
  ]
}
```

**Key Normalization Facts:**

1. **assignments[]** is a flat list with:
   - `assignment_name` (string, unique key)
   - `points_possible` (decimal string or null)

2. **rows[]** has one entry per student:
   - `student` object with id/name/grade_level
   - `scores` is a **dictionary keyed by assignment_name**
     - Each value has `points_earned` and `points_possible`
     - Null `points_earned` = no grade entered yet

3. **Empty states:**
   - No sections: `results: []` from sections endpoint
   - Section with no assignments: `assignments: [], rows: []`
   - Section with assignments but no enrollments: `assignments: [...], rows: []`
   - Enrolled students with no grades: `points_earned: null` in scores

4. **Frontend normalization is ALREADY DONE** - no transformation needed!
   - assignments[] feeds table headers
   - rows[] feeds table body
   - scores dictionary maps assignment_name → cell value

**The payload is render-ready as-is.**

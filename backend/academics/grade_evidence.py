"""One grade-evidence rule for classroom and family readers."""


def resolve_grade(assignment, entry=None, academic=None):
    scored_entry = entry is not None and entry.points_earned is not None
    conflict = bool(scored_entry and (entry.points_possible != assignment.points_possible
                    or academic is not None and entry.points_earned != academic.numeric_score))
    if conflict:
        return {'earned': None, 'possible': assignment.points_possible, 'source': 'conflict_requires_teacher_review', 'conflict': True}
    if scored_entry:
        return {'earned': entry.points_earned, 'possible': entry.points_possible, 'source': 'gradebook.GradeEntry', 'conflict': False}
    return {'earned': academic.numeric_score if academic else None, 'possible': assignment.points_possible,
            'source': 'academics.Grade' if academic else None, 'conflict': False}

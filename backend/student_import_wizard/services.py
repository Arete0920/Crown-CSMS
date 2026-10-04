"""One canonical import writer, with explicit household bridges and reviewed previews."""
import hashlib
import json
import uuid
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from core.models import Family, GradeLevel, HouseholdFamilyLink, Student, StudentIdentityLink
from households.models import Household, Student as CompatibilityStudent

REQUIRED = {'student_number', 'first_name', 'last_name', 'dob', 'status', 'family_id', 'household_id'}
ALLOWED = REQUIRED | {'grade_level', 'compatibility_student_id'}
SCHEMA = 2


def validate_configuration(column_map, rows):
    if not isinstance(column_map, dict) or not column_map:
        raise ValidationError('column_map must be a non-empty object.')
    targets = []
    for column, target in column_map.items():
        if not isinstance(column, str) or not column.strip() or len(column) > 100 or not isinstance(target, str):
            raise ValidationError('Column names and mapped fields must be strings.')
        target = 'student_number' if target == 'external_id' else target
        if target not in ALLOWED:
            raise ValidationError(f'Unsupported canonical student field: {target}.')
        targets.append(target)
    if len(targets) != len(set(targets)):
        raise ValidationError('Each canonical field may be mapped once.')
    missing = REQUIRED - set(targets)
    if missing:
        raise ValidationError(f'Missing canonical fields: {sorted(missing)}.')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000 or any(not isinstance(r, dict) for r in rows):
        raise ValidationError('Stage between 1 and 1000 row objects per reviewed import.')


def snapshot(student):
    return {'student_number': student.student_number, 'first_name': student.first_name,
        'last_name': student.last_name, 'dob': student.dob.isoformat(), 'status': student.status,
        'family_id': str(student.family_id), 'grade_level_id': str(student.current_grade_level_id) if student.current_grade_level_id else None}


def compatibility_snapshot(student):
    return {'id': str(student.id), 'household_id': str(student.household_id), 'first_name': student.first_name,
        'last_name': student.last_name, 'grade_level': student.grade_level, 'is_active': student.is_active}


def prepare(session, lock=False):
    validate_configuration(session.column_map, session.staged_rows)
    school = session.school
    try:
        today = timezone.now().astimezone(ZoneInfo(school.timezone)).date()
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError('Configure a valid school timezone before importing birth dates.')
    prepared = []; review = []; errors = []; seen = set(); seen_compatibility = set()
    for index, row in enumerate(session.staged_rows):
        try:
            values = {}
            for column, target in session.column_map.items():
                value = row.get(column, '')
                if not isinstance(value, str):
                    raise ValidationError(f'{column} must be a string; preserve source identifier formatting.')
                values['student_number' if target == 'external_id' else target] = value.strip()
            if any(not values.get(field) for field in REQUIRED):
                raise ValidationError('Required canonical values must not be blank.')
            number = values['student_number']
            if number in seen:
                raise ValidationError('Duplicate student number within this import.')
            seen.add(number)
            try:
                birth = date.fromisoformat(values['dob'])
                family_id = uuid.UUID(values['family_id']); household_id = uuid.UUID(values['household_id'])
            except (ValueError, TypeError):
                raise ValidationError('Birth date requires ISO format; family and household IDs require UUIDs.')
            if birth > today:
                raise ValidationError('Birth date cannot be in the future on the school calendar.')
            families = Family.objects.filter(school=school, id=family_id, status='ACTIVE')
            households = Household.objects.filter(school_id=school.id, id=household_id)
            bridges = HouseholdFamilyLink.objects.filter(school=school, family_id=family_id, household_id=household_id, family__school=school)
            if lock:
                families = families.select_for_update(); households = households.select_for_update(); bridges = bridges.select_for_update()
            family = families.first(); household = households.first(); bridge = bridges.first()
            if family is None or household is None or bridge is None:
                raise ValidationError('Use an active same-school family, household and explicit family bridge.')
            grade = None
            if values.get('grade_level'):
                grades = GradeLevel.objects.filter(school=school, code=values['grade_level'])
                if lock: grades = grades.select_for_update()
                grade = grades.first()
                if grade is None:
                    raise ValidationError('Grade code must exist in the selected school.')
            students = Student.objects.filter(school=school, student_number=number)
            if lock: students = students.select_for_update()
            student = students.first(); before = snapshot(student) if student else None
            if student and 'grade_level' not in values:
                grades = GradeLevel.objects.filter(school=school, id=student.current_grade_level_id)
                if lock: grades = grades.select_for_update()
                grade = grades.first()
                if student.current_grade_level_id and grade is None:
                    raise ValidationError('Existing grade authority requires school reconciliation.')
            if student and (student.family_id != family_id or student.dob != birth):
                raise ValidationError('Existing student family or birth date differs; resolve identity before importing.')
            links = StudentIdentityLink.objects.filter(school=school, core_student=student) if student else StudentIdentityLink.objects.none()
            if lock: links = links.select_for_update()
            link = links.first(); compatibility = None
            if link:
                compatible = CompatibilityStudent.objects.filter(school_id=school.id, id=link.compatibility_student_id, household=household)
                if lock: compatible = compatible.select_for_update()
                compatibility = compatible.first()
                if link.verification_status != StudentIdentityLink.STATUS_VERIFIED or not link.evidence_reference.strip() or compatibility is None:
                    raise ValidationError('Existing compatibility identity requires reconciliation.')
            supplied_compatibility = values.get('compatibility_student_id')
            if supplied_compatibility:
                try:
                    compatibility_id = uuid.UUID(supplied_compatibility)
                except (ValueError, TypeError):
                    raise ValidationError('compatibility_student_id requires a UUID.')
                if compatibility_id in seen_compatibility:
                    raise ValidationError('Duplicate compatibility identity within this import.')
                seen_compatibility.add(compatibility_id)
                compatible = CompatibilityStudent.objects.filter(school_id=school.id, id=compatibility_id, household=household)
                if lock: compatible = compatible.select_for_update()
                supplied = compatible.first()
                if supplied is None or (link and link.compatibility_student_id != compatibility_id):
                    raise ValidationError('Explicit compatibility identity must retain the same school, household and canonical mapping.')
                assigned = StudentIdentityLink.objects.filter(compatibility_student_id=compatibility_id).first()
                if assigned and (not link or assigned.id != link.id):
                    raise ValidationError('Compatibility identity already has a canonical mapping.')
                if not link and (supplied.first_name.strip().casefold() != values['first_name'].casefold() or supplied.last_name.strip().casefold() != values['last_name'].casefold()):
                    raise ValidationError('Explicit new identity mapping requires matching reviewed source names.')
                compatibility = supplied
            elif student and link is None:
                raise ValidationError('Existing canonical student needs an explicit compatibility mapping before import.')
            elif not student and CompatibilityStudent.objects.filter(school_id=school.id, household=household, core_identity_link__isnull=True).exists():
                raise ValidationError('Unmapped household student identities require explicit compatibility IDs before adding an import identity.')
            old_compatibility = compatibility_snapshot(compatibility) if compatibility else None
            student = student or Student(school=school, family=family, student_number=number)
            student.first_name = values['first_name']; student.last_name = values['last_name']; student.dob = birth
            student.status = values['status']; student.current_grade_level = grade
            student.full_clean()
            # Compatibility identity has a narrower name field than the canonical model.
            if len(student.first_name) > 80 or len(student.last_name) > 80:
                raise ValidationError('Names must fit the 80-character compatibility identity fields.')
            after = snapshot(student)
            item = {'row': index, 'action': 'update' if before else 'create', 'before': before, 'after': after,
                'household_id': str(household.id), 'bridge_id': str(bridge.id),
                'core_updated_at': student.updated_at.isoformat() if before else None,
                'compatibility_before': old_compatibility, 'identity_link_id': str(link.id) if link else None,
                'identity_evidence': link.evidence_reference if link else None}
            item['grade_code'] = grade.code if grade else ''
            review.append(item)
            prepared.append((student, compatibility, household, grade, link, item))
        except ValidationError as exc:
            errors.append({'row': index, 'messages': exc.messages})
    payload = {'schema': SCHEMA, 'school_id': str(school.id), 'column_map': session.column_map,
        'staged_rows': session.staged_rows, 'review': review, 'errors': errors}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return prepared, {'schema': SCHEMA, 'valid': len(review), 'errors': errors, 'rows': review, 'fingerprint': fingerprint}


@transaction.atomic
def write_prepared(session, prepared, actor, reason, fingerprint):
    records = []
    for student, compatibility, household, grade, link, item in prepared:
        student.save()
        compatibility = compatibility or CompatibilityStudent(school_id=session.school_id, household=household)
        compatibility.first_name = student.first_name; compatibility.last_name = student.last_name
        compatibility.grade_level = grade.code if grade else ''; compatibility.is_active = student.status == 'ACTIVE'
        compatibility.full_clean(); compatibility.save()
        if link is None:
            link = StudentIdentityLink.objects.create(school=session.school, core_student=student,
                compatibility_student=compatibility, source=StudentIdentityLink.SOURCE_IMPORT,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference=f'student-import:{session.id}:row:{item["row"]}')
        records.append({**item, 'student_id': str(student.id), 'compatibility_student_id': str(compatibility.id),
            'identity_link_id': str(link.id), 'compatibility_after': compatibility_snapshot(compatibility)})
    return {'schema': SCHEMA, 'created': sum(r['action'] == 'create' for r in records),
        'updated': sum(r['action'] == 'update' for r in records), 'skipped': 0, 'errors': [],
        'records': records, 'fingerprint': fingerprint, 'actor_id': str(actor.id), 'reason': reason,
        'recorded_at': timezone.now().isoformat()}


def reconcile(session):
    result = session.commit_result or {}
    if result.get('schema') != SCHEMA or not result.get('records'):
        raise ValidationError('Earlier import evidence requires reconciliation; canonical verification is unavailable.')
    differences = []
    for record in result['records']:
        student = Student.objects.filter(school=session.school, id=record['student_id']).first()
        compatibility = CompatibilityStudent.objects.filter(school_id=session.school_id, id=record['compatibility_student_id']).first()
        link = StudentIdentityLink.objects.filter(school=session.school, id=record['identity_link_id'],
            core_student_id=record['student_id'], compatibility_student_id=record['compatibility_student_id'],
            verification_status=StudentIdentityLink.STATUS_VERIFIED).first()
        bridge = HouseholdFamilyLink.objects.filter(school=session.school, family_id=record['after']['family_id'],
            household_id=record['household_id'], family__school=session.school).exists()
        household_exists = Household.objects.filter(school_id=session.school_id, id=record['household_id']).exists()
        grade_matches = student and (GradeLevel.objects.filter(school=session.school, id=student.current_grade_level_id, code=record['grade_code']).exists() if student.current_grade_level_id else not record['grade_code'])
        if not student or snapshot(student) != record['after'] or not compatibility or compatibility_snapshot(compatibility) != record['compatibility_after'] or not link or not link.evidence_reference.strip() or not bridge or not household_exists or not grade_matches:
            differences.append({'row': record['row'], 'student_id': record['student_id'], 'detail': 'Canonical row, compatibility identity or family bridge changed.'})
    return {'verified': not differences, 'verified_count': len(result['records'])-len(differences), 'differences': differences}

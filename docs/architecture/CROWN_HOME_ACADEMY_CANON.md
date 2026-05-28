# CROWN Home Academy Canon

Status: Architecture and product-control canon
Updated: 2026-05-28
Module key: `home_academy`

## Purpose

The Home Academy module is a premium optional CROWN module that lets Christian schools operate their own school-branded homeschool affiliation, hybrid academy, course-only, activity, and diploma-track programs.

CROWN is the infrastructure layer. The school owns the public program brand.

Examples:

- `[School Name] Home Academy`
- `[School Name] Hybrid Academy`
- `[School Name] Homeschool Partnership`
- `[School Name] Satellite Program`

## Product boundary

Home Academy is not a CROWN-branded school and not a free-form homeschool curriculum marketplace.

The module must preserve school control over:

- approved academic catalog
- course-delivery variants
- homeschool affiliation status
- school-of-record status
- diploma eligibility status
- sports and activity eligibility
- seat and roster capacity
- required forms and agreements
- billing and financial-aid rules
- transcript and diploma controls

## Baseline CROWN economics

Every active homeschool-affiliated student remains a standard active CROWN student account.

Default platform economics:

- `$29.00` setup fee per student
- `$8.00` per active student per month

The school may add its own charges for courses, labs, sports, activities, chapel/student life, transcript review, graduation audit, diploma-track service, uniforms, materials, or events.

## Required enrollment statuses

The module must distinguish the student's relationship to the school.

Canonical statuses:

- `standard_enrollment`
- `homeschool_affiliate`
- `homeschool_course_only`
- `homeschool_lab_only`
- `homeschool_hybrid`
- `homeschool_school_of_record`
- `homeschool_diploma_track`
- `homeschool_support_only`

## School-of-record and diploma guardrail

Diploma eligibility is not implied by homeschool affiliation.

Required statuses:

- `parent_is_record`
- `school_is_record`
- `outside_school_is_record`
- `none`

Diploma eligibility states:

- `not_eligible`
- `eligible_pending`
- `eligible_approved`
- `not_approved`

The module must not post official transcript credit or indicate school-issued diploma eligibility unless the student's school-of-record and diploma-track controls support that action.

## Offering Catalog

The core object is `Offering`, not `Course`.

Canonical offering types:

- `academic_course`
- `lab`
- `sport`
- `music`
- `drama`
- `art`
- `chapel`
- `club`
- `student_life`
- `event`
- `testing`
- `transcript_review`
- `graduation_audit`
- `dual_enrollment_support`

Each offering must define whether it is credit-bearing, transcript-eligible, diploma-track eligible, capacity-controlled, aid-eligible, and subject to academic-anchor requirements.

## Academic-anchor rule

Home Academy is flexible but not unrestricted.

Default policy:

- Sports require at least two school-approved academic courses in the same term, or school-of-record/diploma-track status.
- Music, drama, art, and major activities require at least one school-approved academic course, lab, or academic package in the same term.
- Chapel and student-life access require at least base affiliation and may be further restricted by school policy.
- Labs must map to an approved academic course or approved lab package.
- Activity-only or sports-only enrollment is blocked by default.

## Capacity protection

Full-time enrolled students retain priority.

Every offering must support:

- total capacity
- full-time reserved seats
- homeschool released seats
- buffer seats
- waitlist permission
- admin override permission

No homeschool student should consume a full-time seat unless the school explicitly releases that seat.

## Required gates

Registration into an offering must pass all enabled gates:

1. active CROWN subscription
2. required form completion
3. payment status
4. academic-anchor rule
5. capacity rule
6. grade/age/prerequisite rule
7. admin, coach, director, or registrar approval when required

## Financial aid rule

Homeschool families may use the same CROWN financial-aid intake process, but aid must be charge-level and school-controlled.

Default aid posture:

- academic courses: aid eligible
- labs: aid eligible
- diploma-track services: aid eligible when school policy allows
- sports and arts: limited aid only after academic anchor is met
- activity-only participation: not aid eligible by default
- uniforms, costumes, equipment, and optional events: usually not aid eligible

## Transcript guardrail

Offering completion must not post directly to the official transcript.

Required workflow:

1. offering completed
2. credit-bearing check
3. transcript-eligible check
4. registrar review
5. transcript category assigned
6. credit value confirmed
7. grade source confirmed
8. posted to transcript
9. locked

## Diploma guardrail

Diploma workflow is later-phase scope.

Required controls before any completion claim:

- school-of-record status
- diploma-track declaration
- approved course plan
- graduation requirement template
- GPA and credit audit
- Bible, chapel, service, or capstone requirements if school policy requires them
- registrar approval
- head-of-school approval
- diploma issuance record

## Implementation order

1. governance entry
2. canon and API/data contract
3. module entitlement key
4. program and enrollment status models
5. offering catalog
6. eligibility gate
7. capacity gate
8. billing and financial-aid charge rules
9. parent and admin dashboard labels
10. attendance and campus-safety extensions
11. academic record staging
12. diploma-track workflow

## Proof gate

The module cannot be marked complete until proof exists for:

- tenant scoping
- RBAC
- migration integrity
- service-level eligibility logic
- service-level capacity logic
- API route availability
- parent/admin labels
- billing classification
- financial-aid classification
- no sports-only default pathway
- no art-only default pathway
- full-time capacity protection
- transcript guardrails

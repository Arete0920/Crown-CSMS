# Runtime Evidence Checklist

Related: #1274 and #1374

This file is a checklist only and does not claim that runtime proof exists.

## Required route matrix

| Persona | Route | Status |
| --- | --- | --- |
| school administrator | `/school-admin-dashboard` | MISSING |
| school administrator | `/admin` | MISSING |
| school administrator | `/dash/admin` | MISSING |
| teacher | `/teacher` | MISSING |
| teacher | `/dash/teacher` | MISSING |
| parent | `/parent` | MISSING |
| parent | `/dash/parent` | MISSING |

## Required evidence per route

- exact frontend identity
- exact backend identity
- final URL
- authenticated screenshot reference
- browser network record
- observed API calls
- failed request count
- console error and warning counts
- authenticated role behavior
- tenant or school-context result
- data-source classification: live, fallback, stub, sample, partial-live, or no-proof
- disposition: PASS, REVIEW, FAIL, or DEFER
- notes and linked evidence artifact

## PASS rule

A route may pass only when all evidence comes from the same unchanged deployed frontend and backend identities. Repository configuration, route registration, source inspection, or unauthenticated evidence cannot substitute for an authenticated browser result.

This checklist does not authorize production or close #1274.
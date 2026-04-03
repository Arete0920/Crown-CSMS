# Changelog

All notable changes to Crown are documented here.

## [Unreleased] - Investor Release Readiness Sprint

### Release Governance and Evidence (Phase 3)

- Added final release-gate truth document with condition-level PASS/PARTIAL/manual statuses
- Added final investor evidence index with explicit evidence presence and ownership
- Added branch protection evidence and security-gate evidence documents
- Added final signoff checklist and known-gaps/deferred register
- Added investor review guide and OpenAPI documentation readme
- Finalized docs navigation and investor-facing README hardening

### Security

- Removed advisory behavior from CodeQL and restored blocking analysis intent
- Added deterministic dependency audit workflow using pip-audit and npm audit
- Repaired production health workflow behavior and aligned it to current health payloads

### Backend

- Wired OpenAPI schema generation and Swagger/ReDoc endpoints
- Added investor-proof tests for admissions, enrollment, billing, attendance, and tenant boundaries
- Added load-test scaffolding and admin scripts for release-readiness operations

### Documentation

- Added repository README, security policy, compliance framework, module inventory, and alert runbook
- Added workflow consolidation plan for reducing CI surface area

## [0.4.0-rc1] - 2026-02-21

### Added

- Deploy contract restoration and production deploy-contract verification workflow
- Additional CI gate enforcement on backend and frontend pipelines

### Security

- Removed secrets from git history via BFG Repo-Cleaner
- Removed tracked production log directories and archives from history
- Rotated exposed credentials

### Fixed

- Health check curl command updated to follow redirects

## [0.3.0] - 2026-01-15

### Added

- Financial aid processing workflow
- Parent portal consolidation
- Billing automation via CompuWerx
- Role-based dashboard system
- Faith module foundation

## [0.2.0] - 2025-11-30

### Added

- Admissions workflow
- Attendance module
- Gradebook basics
- Communications features

## [0.1.0] - 2025-09-01

### Added

- Initial Django, React, PostgreSQL platform scaffold
- JWT and MSAL-based authentication
- School administration basics
- Azure production infrastructure and CI/CD
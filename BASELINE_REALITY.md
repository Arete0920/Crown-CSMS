# Crown2026 Baseline Reality Snapshot
**Date:** 2026-02-02
**Branch:** release/feb16-freeze
**Purpose:** Freeze current truth. No spin. No promises.

## 1) WORKING TODAY (demonstrable without apology)
- [x] App boots (DEV)
- [x] Health endpoint returns 200
- [x] Auth token works for demo user
- [ ] Tenant header enforced (X-School-Id)
- [ ] Admissions: pipeline + drilldown
- [ ] Financial Aid: summary
- [ ] Billing/Tuition: summary
- [ ] Attendance: summary
- [ ] Communications: read-only threads/messages (if applicable)

## 2) UNSTABLE / DO NOT TOUCH TONIGHT
- [ ] DEV smoke fails on Director permission (role assignment)
- [ ] Auth token occasionally times out (slow response)
- [ ] Azure deployment propagation/restart is flaky

## 3) DEFERRED (INTENTIONALLY, not abandoned)
- [ ] Food Services
- [ ] Athletics
- [ ] Daily Devotions
- [ ] Curriculum mapping / scope & sequence
- [ ] Portrait of the Graduate builder (full)
- [ ] Marketplace
- [ ] Surveys/sentiment engine
- [ ] Mobile app/PWA
- [ ] Advanced analytics dashboards

## 4) OPEN RISKS (short, factual)
- [x] CI billing risk (schedules disabled tonight)
- [x] Azure deployment drift risk (if any)
- [ ] Any known security/config gaps (if any)

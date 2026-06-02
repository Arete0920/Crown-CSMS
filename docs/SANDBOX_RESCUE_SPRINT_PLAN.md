# Crown2026 Rescue Sprint Plan

**Goal**: Survive 120-school sandbox + reach stable production in 4 weeks.

## Sprint 0: Emergency Sandbox (0-48h)
- Enable VITE_SANDBOX_READY_ONLY=true + VITE_HIDE_UNREADY_NAV=true
- Add "Sandbox Preview – Features Limited" banners
- Deploy to sandbox environment
- Create KNOWN_LIMITATIONS live page
- Daily status updates

## Sprint 1: Stabilization (Week 1)
- Fix deploy-prod.yml heredoc bug
- Align branches/Codespaces
- Complete core dashboards live data
- Obtain founder signoff
- Close #863/#865

## Sprint 2: Hardening (Weeks 2-3)
- Full E2E tests
- Cross-module plumbing
- Add Mermaid architecture diagrams
- CI/CD approvals
- Load testing

## Sprint 3: Scale (Week 4)
- Observability
- SOC2 prep
- Formal release

**Daily Discipline**: Run full gates + evidence pack update.
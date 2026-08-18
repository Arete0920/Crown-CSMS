# Buyer Operational Transfer Register

**Status:** Active owner-turnover preparation control  
**Last reconciled:** 2026-08-18  
**Current repository identity:** governed by `docs/CURRENT_RELEASE_STATUS.md` and exact current `main`  
**Controlling authority:** `docs/CURRENT_RELEASE_STATUS.md`

## Required asset record

For every transferred repository, cloud resource, domain, certificate, tenant, database, backup, monitoring destination, vendor account, agreement, integration, and support channel, record:

- current and successor owner;
- technical custodian;
- environment and asset identifier;
- access method without secret values;
- dependencies and data categories;
- billing, renewal, region, agreement, and support authority;
- backup, recovery, monitoring, and incident dependencies;
- transfer action and date;
- successor verification result;
- seller-access removal date;
- exception, residual risk, and acceptance authority.

## Required technical acceptance evidence

Before final operational acceptance, the transfer record should identify the exact current repository/release SHA and, where applicable:

1. deployed runtime identity and health evidence;
2. monitoring ownership and notification routing;
3. immutable application rollback evidence or explicit accepted disposition;
4. operational backup/restore evidence or explicit accepted disposition;
5. successor-controlled credentials, recovery factors, and administrative ownership;
6. clean-clone/setup/deploy/recovery instructions exercised to the level required by the transfer agreement;
7. current open issues classified as release blocker, accepted residual risk, roadmap, architecture follow-up, external dependency, or nonblocking technical debt.

## Blocking conditions

Turnover is prohibited while any material asset has unknown ownership, seller-only access that has no approved transition path, unverified billing or renewal authority, missing required agreement, unexplained runtime identity mismatch, unresolved release-blocking security/privacy contradiction, incomplete operating instructions for a required capability, or unaccepted material residual risk.

Repository transfer, repository certification, production authorization, legal/compliance review, and operational acceptance are separate decisions. Historical predecessor release evidence must not be substituted for current Crown-CSMS transfer evidence.
# Buyer Operational Transfer Register

**Status:** Preparation control; buyer turnover is not yet authorized  
**Last reconciled:** 2026-08-09  
**Repository baseline:** `ef9e1fa4f06d6600d60313059f35c0bb564f5a5b`  
**Certified backend:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`  
**Controlling authority:** GitHub issue #1619

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

## Blocking conditions

Turnover is prohibited while any material asset has unknown ownership, seller-only access, unverified billing or renewal authority, missing required agreement, runtime identity mismatch, unresolved critical security/privacy contradiction, incomplete operating instructions, or unaccepted residual risk.

Production authorization and buyer turnover are separate decisions. Repository transfer alone does not establish operational acceptance.

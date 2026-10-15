# Jireh financial aid website — product-family migration contract
Date: 2026-10-15
Decision: One dedicated **Jireh Financial Aid** public website; CROWN Jireh school financial aid is the primary offering and related **Jireh SGO** is a separate pilot-development capability. This supersedes an SGO-only website plan.

## Product boundaries
- CROWN Jireh: school-controlled mission-aligned aid applications, analysis, recommendations, approvals, communication, renewal and reconciliation. Verify functionality against exact source release and a witnessed demonstration before claiming availability.
- Jireh SGO: independent grantor-administered scholarships, with separate eligibility, funding, legal, operational and release authority. Product in pilot development. Never claim actual disbursement or independent tax approval.
- School aid is neither SGO funding nor a cleared payment. Nothing on this website enables real financial processing.

## Content migration scope
Ingest and reconcile https://areteadvisorygroup.com/jireh, https://areteadvisorygroup.com/jireh-sgo, and approved PDF and brand assets. The staging HTML intentionally links to legacy files, contact, privacy and terms until approved copies and replacement routes are available. Source exports and a full asset census are release blockers.

## Arete website reduction AFTER dedicated Jireh domain go-live
Keep Arete's Mission-Aligned Financial Aid advisory framework, a short product-family summary, one CTA to the dedicated Jireh domain, a concise status distinction, and contact path. Keep Arete's independent scholarship-readiness educational content where genuinely advisory. Move detailed product features, intended workflows, FAQs, screenshots, SGO explanations, software-related pricing and demo CTAs to Jireh. Retain Arete's consulting pricing and financial aid thought leadership; do not delete it.
Convert https://areteadvisorygroup.com/jireh and /jireh-sgo to concise navigation pages or appropriate permanent redirects only after the new site's content, domain, and SEO migration are verified. Use one-to-one 301/308 redirects for replaced materials, retain stable educational pages, verify canonical, sitemap, links and query parameters, and keep legacy paths reachable for a documented transition period. Never create a redirect chain or break existing inbound references. Update homepage, software solutions, programs, pricing, contact templates, and footer to point to the dedicated site once live. Until cutover, do not alter the current Arete website.

## Demo registration
Both school-aid and SGO pilot CTA currently route to the existing contact page. This is NOT independently verified as a persistent booking system. Dedicated form/API, first-party lead database, spam defense, confirmation, owner notification, sales workflow, consent/privacy, calendar and failure tests are required before presenting 'schedule a demo' as an actual reservation.

## Infrastructure release blockers
Authenticated Azure inventory, RBAC, tenant, subscription, MFA/recovery, SKU/consumption cost, quotas, budget, DNS and mail export; real-domain and TLS validation; signed-off recurring cost; asset/brand parity; accessibility and actual browser tests; rollback and lead-flow evidence; final content and legal approval. Do not change DNS, GoDaddy domain registration or email before these pass.

## Source layout
Staging source remains at `sites/jireh-sgo` for this initial PR, with full Jireh content. Rename to `sites/jireh` only in a separately tested file-move with deployment path and CI updated, before a first Azure deploy. A non-indexed staging page is not a release.

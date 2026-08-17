# CROWN Known Limitations and Release Disposition

**Last reconciled:** 2026-08-17  
**Controlling authority:** `docs/CURRENT_RELEASE_STATUS.md` and Crown-CSMS issue #14

## Evidence boundary

- The exact GitHub `main` commit being handed off is the current source identity; predecessor tags and historical certification SHAs are not current authority.
- Repository/source certification does not by itself establish a production deployment or runtime identity.
- External payment processing is not selected, contracted, enabled, or certified and remains fail closed.
- Legal, regulatory, tax, accounting, insurance, privacy, accessibility, and contractual conclusions require appropriate qualified review.

## Accepted residual and successor-controlled work

The following are not to be silently represented as completed merely because the repository is transferred:

- production deployment/runtime identity where no exact source-to-runtime proof has been established;
- successor-controlled account creation, access transfer, credential/recovery-factor rotation, and seller-access revocation;
- clean-clone deployment, monitoring, rollback, restore, and incident exercises where operational infrastructure is part of the transfer;
- payment-provider selection, implementation, certification, settlement/refund/dispute operations, and activation;
- vendor, DPA, region, subprocessor, jurisdiction, and contractual reconciliation requiring qualified owner/legal review;
- any product capability explicitly tracked as a post-handoff enhancement or bounded integration rather than a release-blocking defect.

## Product-scope disclosure

Little Lambs currently requires explicit product-authority reconciliation beyond treating the surface as an Aftercare alias. Do not represent a distinct daycare product authority as complete unless issue #81 or successor evidence establishes it.

Communications integrations that depend on external Microsoft 365/Teams, SMS-provider, tenant credentials, consent policy, or provider configuration must be verified in the successor's actual environment before representing those external delivery paths as operational.

## Security and tenant boundary

Known release-blocking authorization, tenant-isolation, and sensitive-data defects discovered during final repository reconciliation must be closed by merged current-main repairs and exact-main evidence before a production-ready repository claim. Open issues that are retained after handoff must clearly identify whether they are accepted residual architecture/integration work, process improvement, or an actual unresolved production blocker.

CROWN is not represented as FERPA certified, COPPA certified, regulator approved, universally compliant, or legally approved for every intended market.

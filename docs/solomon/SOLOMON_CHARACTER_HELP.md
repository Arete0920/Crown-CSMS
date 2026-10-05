# Solomon contextual help character

## Outcome and authority

User-authorized full-body Solomon replaces question-mark help and represents contextual navigation, answers, and directions throughout CROWN. Base: `f2d4772b5df50ff6faf0322fd74889e5de7a7c9b`. Decision owner: John C. Megahan. This is one reversible frontend change; backend, permissions, payment processing, credentials, dependencies, and deployment configuration are outside its scope.

## Design and implementation

Five transparent WebP poses: Guide, Explain, Review, Caution/Discernment, Success. Guide identifies help controls; Review accompanies loading; Explain accompanies published guidance; Caution accompanies retrieval errors. Success is available for explicitly confirmed outcomes; it is not inferred from a successful help request. Character artwork was synthesized for this project and optimized into five small assets. No third-party character or reference artwork was supplied.

`HelpTooltip` is the shared help-bubble control. Use its existing `slug` prop for an exact governed help article. `SolomonContextHelp` resolves fixed route/module identifiers for page guidance. `SolomonCharacter` supplies the shared artwork for other approved help surfaces. A “Meet Solomon” action in every help panel opens a friendly introduction explaining his biblical name, navigation role, contextual answers, and workflow directions. “Back to page help” restores the same guidance without another request. The introduction is available even when a topic has no published help. It is user-opened and does not interrupt work.

The default control includes visible “Solomon” text and an accessible help label.

The launch topbar, dashboard hero Help control, shared wizard shell, and admissions help notice use Solomon. Future contextual help controls should reuse these components. Data-chart hover labels and destructive buttons are not help bubbles.

The panel uses native modal dialog focus containment and Escape support, explicit Close, responsive sizing, loading/error/empty states, cancellation of stale requests, unique control IDs, and plain-text rendering. Animation is one short greeting on hover and one short panel entrance; both are disabled under reduced-motion preferences. Published article text remains the backend source of truth. Existing school support instructions remain available.

Only a help slug or allowlisted static route/module is included in the guidance request. URL query values, record identifiers, student/parent records, financial records, and form values are not forwarded. The existing authenticated API client supplies its normal authentication and school context. This interface does not add model calls or free-text question submission.

The shared panel also hosts optional structured staff guidance from the protected
`/api/solomon/guidance/` endpoint introduced in #85. `VITE_SOLOMON_GUIDANCE_ENABLED`
defaults off; the backend retains its own independent flags and school role/tenant
checks. The frontend uses CROWN’s role adapter and canonical API transport, accepts
only a fixed topic and review acknowledgement, renders curated text plainly, and
rejects responses labeled generated or missing human-review requirements. Parent,
student and unknown roles have no staff controls. Missing backend enablement has
an explicit unavailable state. No external provider is configured. See
[AI privacy boundary](SOLOMON_AI_PRIVACY_BOUNDARY.md) for activation requirements.

## Validation and limits

Focused tests cover lazy loading, safe rendering, retries, empty content, cancellation, focus return, and fixed route mappings. The frontend unit suite, build, lint, and central visual-token scanner must pass for the final change. A native-browser UI contract is provided in `tests/ui/solomon-context-help.spec.ts`; it uses stubbed guidance and is not deployed backend proof.

The smoke command includes the native Solomon contract alongside existing page
proof. Its Playwright web-server configuration enables structured guidance only
for that stubbed test lane; this does not enable the production build. Closed
dialogs contain no hidden headings, and the open dialog receives keyboard focus.

Native-browser verification was blocked locally: no installed Chromium executable, and the browser download returned invalid archives. Native focus containment, mobile appearance, and reduced-motion behavior therefore remain NOT VERIFIED until that browser contract executes successfully. No deployed environment or published-help coverage is certified here. An unpublished or absent topic displays an honest empty state rather than invented guidance.

Rollback: revert the single Solomon-character integration commit. No schema or data rollback is required.

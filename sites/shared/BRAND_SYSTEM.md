# Arete product-family website design system (v1)

Status: staged implementation in Jireh; template for Diadem, Kairos and CROWN (not yet deployed to those products).

## Shared brand tokens
| Token | Color | Purpose |
| --- | --- | --- |
| Navy | `#173746` | Headlines, navigation, footer |
| Teal | `#1c6064` | Subheads and feature emphasis |
| Gold | `#d39c49` | Premium/mission accents |
| Light gold | `#f3c979` | High-visibility primary conversion action |
| Warm cream | `#fcf8f0` | Hero background |
| Light sage | `#edf5f3` | Hero field and secondary surfaces |
| White | `#ffffff` | Content surfaces |

Source of truth: `sites/shared/product-theme.css`. Font system: Georgia display paired with Arial/Helvetica body, no licensed font dependency. Use a bright, school-centered visual experience rather than full-bleed dark corporate hero backgrounds.

## Hero conversion pattern
1. Eyebrow identifies relationship to Arete/CROWN.
2. Oversized outcome-centered two-line headline, distinct to each product.
3. School-centered supporting promise; never imply unavailable features are live.
4. Primary CTA visible without scrolling on large screens and near opening on mobile.
5. Secondary CTA explores documented features.
6. Right-hand visual uses licensed school imagery or product-specific **clearly labeled illustrative** artwork. Do not use fabricated outcomes or unverified screenshots.
7. Trust/authority differentiator under CTAs.
8. Matching high-contrast closing CTA at bottom of page.

## Template hero messages
| Site | Primary message | CTA | Secondary |
| --- | --- | --- | --- |
| Arete | Stronger Christian schools. Clearer decisions. | Start a conversation | Explore our work |
| Jireh | Provision with Purpose. Stewardship with Wisdom. | Request a Jireh demonstration | Explore school financial aid |
| Diadem | Faith-centered care. Confident daily operations. | Request a Diadem demonstration | Explore daycare tools |
| Kairos | Make time for what matters most. | Request a Kairos demonstration | Explore scheduling |
| CROWN | One connected school. More time for your mission. | Request a CROWN demonstration | Explore the platform |

Hero copy is a design proposal except for established Arete and Jireh language. Final claims and claims-approval records govern public text.

## Shared experience requirements
Consistent white top navigation, product identifier, desktop and keyboard-accessible mobile menus, one primary CTA, section spacing, feature cards, legal navigation and footer. Responsive at 320px, 375px, 768px, 1024px and 1440px, with WCAG AA manual review and no horizontal overflow. Reusable shared CSS is versioned once and consumed by future product-site builds; product-specific overrides are permitted only for identity/artwork, not different layout conventions. Honor reduced motion and visible focus.

## Site-reduction rule
After dedicated Jireh goes live, Arete retains a short product overview, referral CTA, approved advisory services and research. Detailed product workflows, FAQs, SGO design-partner copy and demonstration sales funnels live at Jireh. Plan one-to-one redirects, analytics attribution and canonical SEO before removing old Arete pages.

## Open production gates
No Azure resource access or DNS connector, no owned image/PDF export, no authenticated deployment or browser acceptance against actual Azure staging, and no certified registration backend. No domain cutover or release claim until these are evidenced.

# CROWN VISUAL CANON

**Version:** 1.0
**Status:** Frozen Design Governance Document
**Authority:** Platform UI/UX Standard

---

## 1. Design Philosophy

Crown is:
- Institutional, not trendy
- Modern, not flashy
- Structured, not cluttered
- Calm, not chaotic
- Professional, not church-bulletin

The visual system must communicate:

**Strength. Trust. Stability. Mission seriousness.**

---

## 2. Color System (Locked)

### 2.1 Primary Brand Colors

| Role | Hex | Usage |
|------|-----|-------|
| Crown Navy | `#0F2C4C` | Primary headers, sidebar background |
| Crown Blue | `#1C4E80` | Primary buttons, active states |
| Crown Gold Accent | `#C6A54A` | Highlights, key accents |
| Slate Dark | `#1F2933` | Primary text |
| Slate Medium | `#52606D` | Secondary text |
| Light Background | `#F4F6F8` | Page background |
| Card White | `#FFFFFF` | Cards and panels |
| Border Neutral | `#E1E5EA` | Dividers and borders |

**No additional brand colors are allowed without a canon update.**

### 2.2 Accent Rules for Sub-Systems

**Compass**
- Uses Crown base palette
- Gold accent slightly emphasized for KPI highlights
- No alternate primary color

**Barnabas**
- Base palette remains
- Accent allowed: softer muted gold `#D4B96E`
- May use slightly warmer background tone in banners only

**Solomon**
- Base palette remains
- Minimal accent usage
- Elegant gold for headers

**No module may introduce independent color systems.**

---

## 3. Typography (Locked)

**Primary Font Stack:**

```css
font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
```

**Hierarchy:**

| Element | Size | Weight |
|---------|------|--------|
| H1 | 28px | 600 |
| H2 | 22px | 600 |
| H3 | 18px | 600 |
| Body | 14–16px | 400 |
| Small | 12–13px | 400 |

- No decorative fonts.
- No script fonts.
- No serif body text.

---

## 4. Spacing System (Locked Scale)

**Base spacing unit:** 4px.

**Allowed scale:** `4 / 8 / 12 / 16 / 24 / 32 / 40 / 48`

**No arbitrary spacing values.**

---

## 5. Component Standards

### 5.1 Buttons

**Primary Button:**
- Background: Crown Blue
- Text: White
- Border radius: 6px
- Hover: darken 5–8%

**Secondary Button:**
- Border: Crown Blue
- Text: Crown Blue
- Background: transparent

**Danger:**
- Reserved only for destructive actions
- Controlled red (not bright)

**No more than 3 button styles allowed.**

### 5.2 Cards

- Background: White
- Border: 1px neutral border
- Radius: 8px
- Shadow: subtle, low elevation only
- Padding: 16–24px

No heavy shadows.
No glassmorphism.
No neumorphism.

### 5.3 Tables

- Header background: light neutral
- Zebra striping optional but subtle
- Border lines consistent
- Sticky header allowed
- No horizontal overflow without scroll containment

All tables use the same reusable component.

### 5.4 Charts & Graphs

**One chart library only.**

Rules:
- Use Crown Blue as primary series
- Gold for highlight series
- Neutral gray for secondary
- No rainbow color schemes
- No gradient gimmicks
- No 3D effects

Charts must:
- Have clear labels
- Have legends
- Not rely on color alone for meaning

---

## 6. Dashboard Layout Structure (Mandatory)

All dashboards follow:

```
Row 1: KPI Cards (3–6 max)
Row 2: Alerts / Action Items
Row 3: Tables or Operational Detail
Row 4: Trend Charts
```

- Sidebar left.
- Content center.
- No floating panels.

Consistency across all roles.

---

## 7. Navigation Standards

- Sidebar background: Crown Navy
- Active state: slightly lighter blue
- Icons minimal and consistent
- No emoji in navigation
- No mixed icon sets
- Permission-derived nav only.

---

## 8. Barnabas Visual Adjustments

**Barnabas may:**
- Add subtle banner at top of devotion screens
- Use warmer accent in callout boxes
- Use slightly softer background for reflection panels

**Barnabas may NOT:**
- Change layout grid
- Change typography
- Change card system
- Introduce playful graphics

Tone must remain calm and dignified.

---

## 9. Visual Prohibitions

The following are prohibited:
- Inline hex colors in components
- Random Tailwind utility overrides
- Multiple button classes doing similar things
- Inconsistent border radii
- Large drop shadows
- Gradient backgrounds
- Animated dashboards
- Dashboard clutter

---

## 10. Review Protocol

Every major UI PR must confirm:
- Uses CSS variables only
- Uses canonical components
- Follows spacing scale
- Matches dashboard layout doctrine
- No visual drift introduced

---

## 11. Future Amendments

Any new color, layout, or component requires:
- Canon update
- Documentation revision
- Component standardization
- Refactor of old usage if necessary

**No silent divergence.**

---

*Visual Canon v1 Locked*

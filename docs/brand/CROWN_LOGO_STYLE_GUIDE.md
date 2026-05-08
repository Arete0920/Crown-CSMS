# CROWN Logo Style Guide

## Brand

- Product name: **CROWN**
- Descriptor: **Christian School Management Solution**
- Visual tone: premium, calm, trustworthy, Christian school leadership
- Palette: deep royal navy, royal blue, white, warm gold, soft slate

## Approved Logo Assets

| Asset | Path | Usage |
|---|---|---|
| Primary logo lockup | `frontend/dashboards/public/brand/crown-logo-transparent.svg` | Login, sidebar, marketing, printed guides |
| Icon mark | `frontend/dashboards/public/brand/crown-mark-transparent.svg` | Collapsed sidebar, favicon, app icon, small cards |

## Required Product Usage

Use the primary lockup in:

```jsx
<img src="/brand/crown-logo-transparent.svg" alt="CROWN Christian School Management Solution" />
```

Use the icon mark in:

```jsx
<img src="/brand/crown-mark-transparent.svg" alt="" />
```

## Rules

- Use **CROWN**, not Crown2026, in public-facing UI.
- Use **Christian School Management Solution** as the descriptor.
- Do not use emoji crowns.
- Do not use placeholder app badges.
- Do not stretch, recolor, distort, or add shadows to the logo.
- Keep the logo on white, transparent, or very light blue backgrounds.
- Use the icon mark only when the full lockup is too large.

## Color Tokens

```css
--crown-navy: #0B2A5B;
--crown-royal: #2563EB;
--crown-shield-blue: #123C7C;
--crown-gold: #F5B82E;
--crown-slate: #334155;
--crown-bg: #F8FAFC;
```

## Dashboard Placement

- Full logo: upper-left primary sidebar
- Mark only: slim icon rail, favicon, mobile collapsed nav
- No logo footer inside app dashboard

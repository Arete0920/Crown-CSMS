# CROWN Visual System

## Authority

CROWN uses one visual system across authenticated dashboards, the Heritage Christian Academy sandbox entry/session surfaces, production authentication, and public demonstration surfaces.

- `frontend/dashboards/src/styles/crown-theme.css` is the sole authority for design tokens: colors, typography, spacing, radii, shadows, and semantic states.
- `frontend/dashboards/src/styles/launch-shell.css` is the sole authority for dashboard shell layout, navigation, grids, rails, widgets, and responsive behavior.
- `frontend/dashboards/src/styles/crown-wizard.css` may define wizard-specific layout and components, but must consume central tokens.
- `frontend/dashboards/src/styles/crown.css` is legacy compatibility CSS. It must not introduce duplicate token declarations or shared launch-shell component rules.

## Palette

The primary product identity is light royal:

- royal blue for primary actions, navigation emphasis, focus, and selected states;
- white and soft blue surfaces for pages, cards, and panels;
- restrained gold for mission, celebration, and premium emphasis;
- semantic green, amber, and red only for success, warning, and danger states;
- blue-gray text and borders for hierarchy without heavy contrast.

All product colors must resolve through `--crown-*` tokens. Raw color literals are allowed only for documented exceptions such as logos, SVG artwork, chart series, and browser compatibility fallbacks adjacent to a token reference.

## Typography

The authoritative product font stack is:

`Inter, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`

All authenticated dashboards, sandbox surfaces, production authentication, and public demo pages must use this stack directly or inherit it from the root shell. Alternate font families require an explicit documented exception.

## Components

Shared visual patterns must use central classes or token-backed component styles:

- page shell and responsive columns;
- sidebars, topbars, and right rails;
- cards, KPI cards, alerts, tables, forms, and buttons;
- headings, labels, helper text, and status badges;
- spacing, radii, shadows, focus states, and hover states.

New inline visual styling is prohibited when an existing shared class or token-backed component can express the same result.

## Responsive standard

Certified visual review uses:

- desktop: 1440 x 1024;
- tablet: 1024 x 768;
- mobile: 390 x 844.

Every certified dashboard and Heritage sandbox surface must avoid page-level horizontal overflow, clipped controls, overlapping content, unreadable text, and inaccessible navigation at each viewport.

## Enforcement

From `frontend/dashboards`, run `npm run check:visual-system` to scan frontend source for:

- non-authoritative font-family declarations;
- raw color literals outside the authoritative token file and documented exceptions;
- duplicate `--crown-*` token declarations outside `crown-theme.css`;
- inline JSX visual styles requiring migration.

The scanner reports the current migration inventory. CI blocks newly introduced findings above the reviewed baseline once that baseline file is established and reduced to intentional exceptions only.

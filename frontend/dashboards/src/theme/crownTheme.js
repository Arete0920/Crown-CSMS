import { createTheme } from "@mui/material/styles";
import { colors } from "./tokens";

// MUI derives light/dark/contrast palette channels during theme creation and
// therefore requires concrete color values here. CSS custom properties remain
// the styling authority for component and shell rules.
const muiPalette = {
  primary: "#2a5ec4",
  primaryStrong: "#1e4faf",
  primaryDeep: "#173f91",
  success: "#1f7a45",
  warning: "#a86a12",
  danger: "#b4232c",
  text: "#122033",
  neutral: "#42566e",
  border: "#d6e3f5",
  background: "#f8fbff",
  paper: "#ffffff",
};

/**
 * Crown MUI Theme
 * Apply via <ThemeProvider theme={crownTheme}> at the app root.
 * Scoped to MUI components only - existing crown-* CSS classes are unaffected.
 */
export const crownTheme = createTheme({
  palette: {
    primary: { main: muiPalette.primary, dark: muiPalette.primaryDeep },
    success: { main: muiPalette.success },
    warning: { main: muiPalette.warning },
    error: { main: muiPalette.danger },
    text: {
      primary: muiPalette.text,
      secondary: muiPalette.neutral,
    },
    background: {
      default: muiPalette.background,
      paper: muiPalette.paper,
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h1: { fontSize: 28, fontWeight: 600 },
    h2: { fontSize: 20, fontWeight: 600 },
    h3: { fontSize: 16, fontWeight: 600 },
    body1: { fontSize: 14 },
    body2: { fontSize: 12, color: muiPalette.neutral },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          border: `1px solid ${muiPalette.border}`,
          boxShadow: "0 8px 20px var(--crown-compat-color-55abd9e574)",
          transition: "all 150ms ease-in-out",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 12px 24px var(--crown-compat-color-16b1bb0c6f)",
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 500,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          border: `1px solid ${muiPalette.border}`,
          boxShadow: "0 6px 18px var(--crown-compat-color-55abd9e574)",
        },
      },
    },
  },
});

// Retain the exported token object import as an explicit linkage to the CSS
// token authority for non-palette consumers in this module's dependency graph.
void colors;

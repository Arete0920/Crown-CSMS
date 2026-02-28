import { createTheme } from "@mui/material/styles";
import { colors } from "./tokens";

/**
 * Crown MUI Theme
 * Apply via <ThemeProvider theme={crownTheme}> at the app root.
 * Scoped to MUI components only — existing crown-* CSS classes are unaffected.
 */
export const crownTheme = createTheme({
  palette: {
    primary: { main: colors.primary },
    success: { main: colors.success },
    warning: { main: colors.warning },
    error:   { main: colors.danger },
    background: {
      default: colors.background,
      paper:   "#ffffff",
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h1: { fontSize: 28, fontWeight: 600 },
    h2: { fontSize: 20, fontWeight: 600 },
    h3: { fontSize: 16, fontWeight: 600 },
    body1: { fontSize: 14 },
    body2: { fontSize: 12, color: colors.neutral },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          border: `1px solid ${colors.border}`,
          boxShadow: "none",
          transition: "all 150ms ease-in-out",
          "&:hover": {
            transform: "translateY(-2px)",
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
          border: `1px solid ${colors.border}`,
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        },
      },
    },
  },
});

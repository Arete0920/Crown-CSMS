import { createTheme } from "@mui/material/styles";
import { colors } from "./tokens";

/**
 * Crown MUI Theme
 * Apply via <ThemeProvider theme={crownTheme}> at the app root.
 * Scoped to MUI components only - existing crown-* CSS classes are unaffected.
 */
export const crownTheme = createTheme({
  palette: {
    primary: { main: colors.primary, dark: colors.primaryDeep ?? colors.primaryStrong },
    success: { main: colors.success },
    warning: { main: colors.warning },
    error:   { main: colors.danger },
    text: {
      primary: colors.text,
      secondary: colors.neutral,
    },
    background: {
      default: colors.background,
      paper:   colors.paper,
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
          boxShadow: "0 8px 20px rgba(23, 63, 145, 0.08)",
          transition: "all 150ms ease-in-out",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 12px 24px rgba(23, 63, 145, 0.12)",
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
          boxShadow: "0 6px 18px rgba(23, 63, 145, 0.08)",
        },
      },
    },
  },
});

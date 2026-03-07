import js from "@eslint/js";
import globals from "globals";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11y from "eslint-plugin-jsx-a11y";

export default [
  // ignore build artifacts
  { ignores: ["dist/**", "build/**", "node_modules/**"] },

  // base rules
  js.configs.recommended,

  // app rules
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    plugins: {
      react,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "jsx-a11y": jsxA11y,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      // React quality-of-life
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off", // Vite/React doesn't need React import
      "react/jsx-uses-vars": "error", // Tell ESLint that JSX references count as usage
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      // Accessibility (WCAG 2.1 AA baseline — Stage 1 Production Hardening)
      ...jsxA11y.configs.recommended.rules,

      // 🔒 Guardrail: forbid direct fetch() everywhere...
      "no-restricted-globals": ["error", "fetch"],
    },
  },

  // ...except the approved canon files
  {
    files: ["src/utils/authClient.js", "src/lib/api.js"],
    rules: {
      "no-restricted-globals": "off",
    },
  },
];

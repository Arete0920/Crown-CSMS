import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11yX from "eslint-plugin-jsx-a11y-x";

const a11yRecommended = jsxA11yX.configs.recommended;
if (!a11yRecommended?.rules || !a11yRecommended?.plugins) {
  throw new Error("eslint-plugin-jsx-a11y-x did not expose its documented flat configuration");
}

const intrinsicTagName = /^[a-z]/;
const crownReact = {
  rules: {
    "jsx-uses-vars": {
      meta: {
        type: "problem",
        docs: { description: "Mark variables referenced by JSX elements as used" },
        schema: [],
      },
      create(context) {
        return {
JSXOpeningElement(node) {
  if (node.name.type === "JSXNamespacedName") return;
  let name;
  if (node.name.type === "JSXIdentifier") {
    name = node.name.name;
    if (intrinsicTagName.test(name)) return;
  } else if (node.name.type === "JSXMemberExpression") {
    let object = node.name.object;
    while (object?.type === "JSXMemberExpression") object = object.object;
    name = object?.name;
  }
  if (name) context.sourceCode.markVariableAsUsed(name, node);
},
        };
      },
    },
  },
};

export default [
  { ignores: ["dist/**", "build/**", "node_modules/**"] },
  js.configs.recommended,
  {
    files: ["src/**/*.{js,jsx}"],
    ...a11yRecommended,
    languageOptions: {
      ...a11yRecommended.languageOptions,
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: {
        ...a11yRecommended.languageOptions?.parserOptions,
        ecmaFeatures: { jsx: true },
      },
      globals: { ...globals.browser, ...globals.es2021 },
    },
    plugins: {
      ...a11yRecommended.plugins,
      "crown-react": crownReact,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...a11yRecommended.rules,
      ...reactHooks.configs.recommended.rules,
      "no-useless-assignment": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/immutability": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "crown-react/jsx-uses-vars": "error",
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "no-restricted-globals": ["error", "fetch"],
    },
  },
  {
    files: ["src/utils/authClient.js", "src/lib/api.js"],
    rules: { "no-restricted-globals": "off" },
  },
];

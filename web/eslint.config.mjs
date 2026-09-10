import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["node_modules/**", ".next/**", "out/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  { languageOptions: { globals: { ...globals.browser } } },
  {
    files: ["scripts/**/*.mjs"],
    languageOptions: { globals: { ...globals.node }, sourceType: "module" },
  },
);

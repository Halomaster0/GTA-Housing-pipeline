import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // next-env.d.ts is rewritten by `next build` (it appends a routes.d.ts
  // triple-slash reference). Linting a generated file is noise — and it was
  // the PR #47 web-job red: the committed copy post-dated the last local
  // lint run. Never lint it; never hand-edit it.
  { ignores: ["node_modules/**", ".next/**", "out/**", "next-env.d.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  { languageOptions: { globals: { ...globals.browser } } },
  {
    files: ["scripts/**/*.mjs"],
    languageOptions: { globals: { ...globals.node }, sourceType: "module" },
  },
);

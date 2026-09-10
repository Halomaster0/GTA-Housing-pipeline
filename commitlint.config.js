// Conventional Commits enforcement, run via the commitlint pre-commit hook
// (.pre-commit-config.yaml, commit-msg stage) and available to `commitlint`
// directly for anyone who prefers running it by hand.
//
// JS over a `.commitlintrc.yaml`: commitlint's own docs resolve
// `commitlint.config.js` by default ahead of any rc file, so this needs no extra
// `--config` flag anywhere it runs. The repo already carries a Node/JS toolchain
// for the Phase 4b Next.js app (web/), so there is no new language introduced by
// choosing JS here -- see docs/decisions/0001-tooling-and-ci.md.
module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // Conventional Commits default is unbounded; keep subject lines skimmable in
    // `git log --oneline` for the "commits are readable" posture in
    // docs/build-plan.md §0.1.
    "header-max-length": [2, "always", 100],
  },
};

# Gate reports

One file per phase gate, written by `release-manager` and nobody else.

A gate closes only when every acceptance criterion in `docs/build-plan.md` §6 has evidence beside it — a file path or pasted command output. An agent's assertion is not evidence. Verdicts are PASS, FAIL, or CONDITIONAL PASS, and only the CEO can override a FAIL.

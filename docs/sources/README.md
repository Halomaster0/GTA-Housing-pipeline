# Data sources — verification index

**Last verification attempt: 2026-09-10** (`source-scout`). **Result: total block, zero sources
confirmed.** Every canonical host required by this project — across all six source families in
the build plan — was rejected by this session's network egress policy before any application
data was returned. This is not a per-source outage; a control test against unrelated hosts
(`google.com`, `example.com`) failed identically, while `github.com` succeeded, which pins the
cause to an allowlist-based sandbox policy rather than any of these government/municipal sites
being down. Full raw transcript, every command, every response:
[`docs/sources/evidence/2026-09-10-verification.md`](evidence/2026-09-10-verification.md).

Per the CEO's hard rule, no row count, field list, or licence text in the per-source docs below
is asserted as confirmed. Where prior general knowledge is mentioned for context (e.g. "Toronto
commonly publishes under an Open Government Licence variant"), it is explicitly labelled
unverified and excluded from the Gate 1 acceptance claim.

## Index

| Source | Status | Licence | Row count (2026-09-10) | Verified on | Star-schema fields confirmed missing |
|---|---|---|---|---|---|
| [Toronto — CKAN](toronto-ckan.md) | UNVERIFIED-BLOCKED | UNVERIFIED (uncited: "Open Government Licence – Toronto") | UNVERIFIED | Not verified | N/A — no schema was ever read, so nothing can be confirmed *missing* either; the whole field set is unknown |
| [Mississauga — ArcGIS](mississauga-arcgis.md) | UNVERIFIED-BLOCKED | UNVERIFIED | UNVERIFIED | Not verified | N/A — portal hostname itself unconfirmed |
| [Brampton — ArcGIS](brampton-arcgis.md) | UNVERIFIED-BLOCKED | UNVERIFIED | UNVERIFIED | Not verified | N/A — portal hostname itself unconfirmed |
| [Peel Region — ArcGIS](peel-arcgis.md) | UNVERIFIED-BLOCKED | UNVERIFIED | UNVERIFIED | Not verified | N/A — plus a structural caveat: Peel is upper-tier and likely does not issue permits at all (see doc) |
| [Statistics Canada — Census + WDS](statcan.md) | UNVERIFIED-BLOCKED | UNVERIFIED (uncited: "Statistics Canada Open Licence") | UNVERIFIED | Not verified | N/A — no product ID was ever confirmed, per the rule against trusting a remembered ID |
| [CMHC — Housing Starts (optional)](cmhc.md) | NOT ADOPTED (pending; also blocked) | UNVERIFIED | UNVERIFIED | Not verified | N/A — open question is whether a real API exists at all, not which fields it has |

**Row-level detail underlying this table** (per registered check, not per family) is in
`config/sources.yml` and, after any live run, `verification-latest.json` in this directory.

## Verify script

`scripts/verify_sources.py` reads `config/sources.yml` and re-issues a live check per source.
Run it with:
```
uv run --with httpx --with pyyaml python scripts/verify_sources.py
```
Its last run in this environment (2026-09-10, same network conditions as above) exited `1` —
correctly, because every source is genuinely unreachable from here. See the pasted output in the
`source-scout` session report and in `verification-latest.json`.

## CEO escalation

Per role card §5.3 ("Escalates: any source that is dead, licence-ambiguous, or missing a field
the star schema depends on → Chief of Staff, same session"), and per §9 risk R1 ("A source is
retired mid-build ... Trigger to escalate: Any verify-sources failure"):

1. **`scripts/verify_sources.py` failed on every single registered source (10/10) on the first
   run of Phase 1.** That is the exact trigger condition in R1. This session cannot tell whether
   the underlying government/municipal APIs are themselves healthy — only that nothing reachable
   from inside this sandbox could confirm them. **This blocks Gate 1's "every source confirmed
   live with a committed row count and licence" criterion outright**, through no fault in the
   sources themselves as far as this session can tell.
2. **Root cause is environmental, not this project's data sources:** the sandbox's network
   egress policy allowlists a small set of developer-tooling hosts (GitHub, PyPI, npm, and
   Anthropic's own API — see the `noProxy` list in the evidence log §0) and denies all other
   outbound HTTPS, including every government open-data host in scope. Confirmed with two
   independent fetch mechanisms (`curl` through the local agent proxy, and Anthropic-side
   `WebFetch`) and a control test against unrelated non-government hosts.
3. **No licence could be confirmed for any source**, which independently blocks the "licence
   permits public portfolio use" requirement (§5.3) even before row counts are considered. Flag
   this loudly, as instructed: an unconfirmed licence is being treated here as equivalent to an
   ambiguous one for gating purposes — Phase 2 ingestion must not start against any source whose
   licence text has not actually been read.
4. **Decision needed from the CEO / Chief of Staff:** either (a) grant network egress to the
   specific hosts listed in `config/sources.yml` for a future `source-scout` session (or for
   CI, which per the build plan is expected to have normal internet access already — this
   finding is specific to *this* interactive session's sandbox), or (b) explicitly accept that
   Gate 1's "every source confirmed live" criterion cannot close until that access exists, and
   adjust the phase-1 timeline accordingly. Building `config/sources.yml` and
   `scripts/verify_sources.py` now — so that the very next network-enabled run does the real
   verification with zero additional engineering — is this session's answer to "make forward
   progress without pretending the block doesn't exist."
5. No public claim (row count, licence name, "N sources verified") should be made anywhere —
   README, resume bullets, dashboard — based on anything in this docs/sources/ tree as of
   2026-09-10. Every number in it is explicitly UNVERIFIED.

## What is and is not safe to build on this Phase 1 pass

- **Safe to build on:** the registry shape (`config/sources.yml`), the checker
  (`scripts/verify_sources.py`, ruff-clean, exits correctly on total failure), and the
  documentation scaffolding (this index + six per-source docs) — these are real, reusable
  artifacts regardless of network conditions, and they are exactly what a stranger re-running
  verification later needs.
- **Not safe to build on:** any ingestion code (`ingestion-engineer`'s connectors), any gold SQL
  that assumes specific columns exist (`transform-engineer`), or any dashboard/API text that
  states a source is "live." None of that should start until this doc's UNVERIFIED rows have
  real values from a real response.

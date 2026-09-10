# Source verification evidence log — 2026-09-10

**Run by:** `source-scout` · **Session window:** 2026-09-10 06:09–06:12 UTC
**Purpose:** raw, unedited record of every live verification attempt against every candidate
canonical endpoint for the six source families in the build plan (§5.3). This is the file a
skeptical reviewer opens to confirm no row count or licence claim was fabricated.

**Headline result: every single canonical endpoint tested — 17 distinct hosts across all six
source families, plus two neutral control hosts — was rejected by the sandbox's network egress
policy before a single byte of application data was received.** No dataset was confirmed. No
dataset was disproven. The block is at the network layer, in front of every destination, not a
403/404 from the destination servers themselves. See `docs/sources/README.md` §"CEO escalation"
for what this means for Gate 1.

---

## 0. Environment check

Confirmed the outbound path per the task's network notes before testing any real source.

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
```
```json
{
  "enabled": true,
  "port": 41707,
  "caBundlePath": "/root/.ccr/ca-bundle.crt",
  "hasSystemCa": true,
  "bundleCoversEveryHost": true,
  "noProxy": "localhost,127.0.0.1,::1,127.0.0.0/8,0.0.0.0/8,::,169.254.0.0/16,api.anthropic.com,...,registry.npmjs.org,jsr.io,npm.jsr.io,pypi.org,files.pythonhosted.org,index.crates.io,proxy.golang.org,...",
  "selective": false,
  "standalone": false,
  "toolScoped": false,
  "gitConfigInjection": true,
  "gitSshRewrite": true,
  "recentRelayFailures": []
}
```
Proxy itself is up and TLS is fine (`bundleCoversEveryHost: true`). The `noProxy` allowlist shown
here is explicitly limited to Anthropic's own API, package registries (npm/pypi/jsr/crates/go),
and private network ranges — no government or open-data host is on it. That allowlist shape is
the first hint of what the subsequent calls confirm directly.

---

## 1. Toronto — CKAN

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=permit&rows=50"
curl: (56) CONNECT tunnel failed, response 403

HTTP_STATUS:000
```
```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=development%20application&rows=50"
curl: (56) CONNECT tunnel failed, response 403

HTTP_STATUS:000
```
```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=ward&rows=50"
curl: (56) CONNECT tunnel failed, response 403

HTTP_STATUS:000
```
```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=zoning&rows=50"
curl: (56) CONNECT tunnel failed, response 403

HTTP_STATUS:000
```
```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://open.toronto.ca/dataset/building-permits-active-permits/"
curl: (56) CONNECT tunnel failed, response 403

HTTP_STATUS:000
```
Cross-checked with a second, independent fetch path (Anthropic-side WebFetch, not the local
sandbox proxy):
```
WebFetch("https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=permit&rows=5")
→ {"error_type":"EGRESS_BLOCKED","domain":"ckan0.cf.opendata.inter.prod-toronto.ca",
   "message":"Access to ckan0.cf.opendata.inter.prod-toronto.ca is blocked by the network egress proxy."}
```
**Verdict: UNVERIFIED-BLOCKED.** Neither `open.toronto.ca` nor the CKAN API host was reachable
from either fetch path. No package list, no resource IDs, no row counts, no schema, no licence
page were retrieved.

---

## 2. Mississauga — ArcGIS

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://data.mississauga.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://opendata.mississauga.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://hub.arcgis.com/api/v3/datasets?q=mississauga%20building%20permits"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```
**Verdict: UNVERIFIED-BLOCKED.** Could not even resolve which host is the current Mississauga
open-data portal (the plan's suggested `data.mississauga.ca` was tried; ArcGIS Hub discovery
search was tried as a fallback). No feature-layer REST endpoint was ever reached, so no
`?f=json` field list and no `returnCountOnly=true` count exist for this source.

---

## 3. Brampton — ArcGIS

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://geohub.brampton.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://maps.brampton.ca/arcgis/rest/services"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```
**Verdict: UNVERIFIED-BLOCKED.** Same failure mode as Mississauga. No layer discovered, no
count, no schema.

---

## 4. Peel Region — ArcGIS

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://data.peelregion.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://hub.arcgis.com/api/v3/datasets?q=peel%20region%20building%20permits"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```
Cross-checked with WebFetch:
```
WebFetch("https://data.peelregion.ca")
→ {"error_type":"EGRESS_BLOCKED","domain":"data.peelregion.ca",
   "message":"Access to data.peelregion.ca is blocked by the network egress proxy."}
```
**Verdict: UNVERIFIED-BLOCKED.**

---

## 5. Statistics Canada — Census + WDS

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www.statcan.gc.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```
Cross-checked with WebFetch:
```
WebFetch("https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesListLite")
→ {"error_type":"EGRESS_BLOCKED","domain":"www150.statcan.gc.ca",
   "message":"Access to www150.statcan.gc.ca is blocked by the network egress proxy."}
```
**Verdict: UNVERIFIED-BLOCKED.** No cube metadata, no product IDs confirmed. Per the task's own
instruction not to trust remembered product IDs, none are asserted anywhere in the per-source
doc or in `config/sources.yml` — the fields are left explicitly blank/pending.

---

## 6. CMHC (optional)

```
$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www.cmhc-schl.gc.ca"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www03.cmhc-schl.gc.ca/hmip-pimh/en"
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000
```
**Verdict: UNVERIFIED-BLOCKED.**

---

## 7. Control test — is this target-specific or a blanket policy?

To rule out "these specific hosts happen to be down" versus "this sandbox cannot reach the
public internet at all except an allowlist," two unrelated, universally-up hosts were tried,
plus two hosts known to be allowlisted:

```
$ curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" "https://www.google.com" --max-time 15
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" "https://example.com" --max-time 15
curl: (56) CONNECT tunnel failed, response 403
HTTP_STATUS:000

$ curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" "https://github.com" --max-time 15
HTTP_STATUS:400

$ curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" "https://raw.githubusercontent.com" --max-time 15
HTTP_STATUS:301
```
**Conclusion:** `github.com` and `raw.githubusercontent.com` connect fine (they return real HTTP
status codes, not `000`/tunnel failures). `google.com` and `example.com` — generic, unrelated
hosts with no connection to this project — fail with the exact same `CONNECT tunnel failed,
response 403` as every data-source host above. This is **not** a source-specific outage; it is
an allowlist-based egress policy for this session that permits a small set of developer-tooling
hosts (GitHub, package registries, Anthropic's own API — see the `noProxy` list in §0) and
denies everything else, including every government and municipal open-data host this task
requires.

## 8. Proxy-side failure ledger (verbatim, `recentRelayFailures` from the status endpoint)

```json
[
  {"ts":"2026-09-10T06:10:12.036Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www.cmhc-schl.gc.ca:443"},
  {"ts":"2026-09-10T06:10:19.843Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www.google.com:443"},
  {"ts":"2026-09-10T06:10:20.111Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"example.com:443"},
  {"ts":"2026-09-10T06:10:47.163Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"ckan0.cf.opendata.inter.prod-toronto.ca:443"},
  {"ts":"2026-09-10T06:10:48.017Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"open.toronto.ca:443"},
  {"ts":"2026-09-10T06:10:50.118Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"hub.arcgis.com:443"},
  {"ts":"2026-09-10T06:10:50.410Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"data.mississauga.ca:443"},
  {"ts":"2026-09-10T06:10:50.813Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"opendata.mississauga.ca:443"},
  {"ts":"2026-09-10T06:10:51.087Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"geohub.brampton.ca:443"},
  {"ts":"2026-09-10T06:10:51.383Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"maps.brampton.ca:443"},
  {"ts":"2026-09-10T06:10:51.717Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"data.peelregion.ca:443"},
  {"ts":"2026-09-10T06:10:52.052Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"hub.arcgis.com:443"},
  {"ts":"2026-09-10T06:11:01.891Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www150.statcan.gc.ca:443"},
  {"ts":"2026-09-10T06:11:02.189Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www12.statcan.gc.ca:443"},
  {"ts":"2026-09-10T06:11:02.471Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www.statcan.gc.ca:443"},
  {"ts":"2026-09-10T06:11:02.759Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www.cmhc-schl.gc.ca:443"},
  {"ts":"2026-09-10T06:11:03.047Z","kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"www03.cmhc-schl.gc.ca:443"}
]
```

## 9. What was and was not done

- **Was done:** direct live HTTP(S) calls against the canonical API/portal host for every one of
  the six source families, using two independent egress paths (local sandboxed `curl` through
  the agent proxy, and Anthropic-side `WebFetch`), plus a control test against unrelated hosts
  to confirm the failure is a blanket policy and not a per-source outage.
- **Was not done, and must not be treated as done:** no dataset slug, resource ID, ArcGIS layer
  ID, StatCan product ID, field list, licence text, or row count was read from any live
  response, because no live response was ever received. Per the hard rule, none of these are
  guessed from training-data memory and presented as current. Where a per-source doc mentions a
  "commonly published" licence name or a "typically named" dataset, it is explicitly labelled
  **prior general knowledge, NOT verified this session** and is not counted toward Gate 1.
- **Re-run instructions:** once network egress is opened for these hosts (or this is run from
  CI, which per the build plan has normal internet access), re-run exactly:
  `uv run --with httpx --with pyyaml python scripts/verify_sources.py` — this reissues the same
  class of calls recorded in `config/sources.yml` and will populate real counts.

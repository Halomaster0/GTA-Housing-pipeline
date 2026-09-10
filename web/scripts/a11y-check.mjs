/* Static accessibility assertions over the exported site (web/out).
 *
 * Runs in CI with no browser (ADR-0009): one h1 per page, document language,
 * titles, descriptions, table captions, image alts, skip link, main landmark,
 * and the inline map's img role. Lighthouse >= 95 stays the human-verified
 * bar at review time; this script is the floor that never regresses silently.
 *
 * Usage: npm run build && npm run test:a11y
 */

import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const OUT = join(import.meta.dirname, "..", "out");

function collectHtml(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) collectHtml(full, acc);
    else if (entry.name.endsWith(".html")) acc.push(full);
  }
  return acc;
}

function count(re, html) {
  return (html.match(re) ?? []).length;
}

const failures = [];

if (!existsSync(OUT)) {
  console.error(`a11y-check: ${OUT} missing — run \`npm run build\` first.`);
  process.exit(1);
}

const pages = collectHtml(OUT);
if (pages.length === 0) {
  failures.push("no HTML pages found under web/out");
}

for (const page of pages) {
  const html = readFileSync(page, "utf-8");
  const name = page.replace(OUT, "out");
  const check = (ok, msg) => {
    if (!ok) failures.push(`${name}: ${msg}`);
  };

  check(/<html[^>]*\blang="en"/.test(html), "missing <html lang=\"en\">");
  check(count(/<h1[\s>]/g, html) === 1, "must have exactly one <h1>");
  check(/<title>[^<]+<\/title>/.test(html), "missing non-empty <title>");
  check(
    /<meta[^>]*name="description"[^>]*content="[^"]+"/.test(html),
    "missing meta description with content",
  );
  check(
    /<a[^>]*class="skip-link"[^>]*href="#main"/.test(html),
    "missing skip link to #main",
  );
  check(/<main[^>]*id="main"/.test(html), "missing <main id=\"main\">");

  const tables = count(/<table[\s>]/g, html);
  const captions = count(/<caption[\s>]/g, html);
  check(captions >= tables, `${tables} table(s) but only ${captions} caption(s)`);

  const imgs = [...html.matchAll(/<img\b([^>]*)>/g)];
  for (const [, attrs] of imgs) {
    check(/alt="[^"]*"/.test(attrs), "<img> without alt text");
  }
}

const home = readFileSync(join(OUT, "index.html"), "utf-8");
if (!/<svg[^>]*role="img"/.test(home)) {
  failures.push("out/index.html: inline map must carry role=\"img\"");
}

if (failures.length > 0) {
  console.error(`a11y-check: ${failures.length} failure(s) in ${pages.length} page(s):`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}
console.log(`a11y-check: ${pages.length} page(s) pass.`);

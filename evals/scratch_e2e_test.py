"""End-to-end smoke test for the multi-agent query graph."""

import logging
import sys

# Ensure repo root is on the path
sys.path.insert(0, r"C:\Users\Halom\Documents\GTA-Housing-pipeline")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from src.ai.graph import run_query  # noqa: E402

print("=" * 60)
print("TEST 1: Answerable question (Mississauga permits)")
print("=" * 60)
r1 = run_query("How many permits were issued in Mississauga?")
print(f"  is_refusal : {r1.is_refusal}")
print(f"  answer     : {r1.answer[:200]}")
print(f"  sql        : {(r1.sql or '')[:150]}")
print(f"  row_count  : {r1.row_count}")
print(f"  latency_ms : {r1.latency_ms:.0f}")
print()

print("=" * 60)
print("TEST 2: Refusal question (Vancouver — out of scope)")
print("=" * 60)
r2 = run_query("How many permits were issued in Vancouver last year?")
print(f"  is_refusal      : {r2.is_refusal}")
print(f"  refusal_reason  : {r2.refusal_reason}")
print(f"  latency_ms      : {r2.latency_ms:.0f}")
print()

print("=" * 60)
print("TEST 3: Answerable question (Brampton vs Mississauga)")
print("=" * 60)
r3 = run_query("Compare total permits issued in Brampton versus Mississauga.")
print(f"  is_refusal : {r3.is_refusal}")
print(f"  answer     : {r3.answer[:300]}")
print(f"  latency_ms : {r3.latency_ms:.0f}")
print()

print("=" * 60)
print("TEST 4: Refusal — Toronto net units (should answer but note under review)")
print("=" * 60)
r4 = run_query("What is the total net new housing units across the GTA?")
print(f"  is_refusal : {r4.is_refusal}")
print(f"  answer     : {r4.answer[:300]}")
print(f"  latency_ms : {r4.latency_ms:.0f}")
print()

print("All tests done. Check traces/ directory for JSON trace files.")

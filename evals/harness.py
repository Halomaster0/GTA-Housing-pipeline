"""
Evaluation harness for the GTA Housing Pipeline AI query layer.

Loads evals/golden_questions.yaml, runs each question through the
Planner → Executor → Critic graph, scores across 6 buckets, and writes
results to evals/results/{date}-{git_sha}.json.

Usage:
    uv run python evals/harness.py
    uv run python evals/harness.py --limit 10   # quick smoke run
    uv run python evals/harness.py --bucket simple_aggregate
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

# Ensure repo root on sys.path when run directly
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.ai.graph import QueryResponse, run_query  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("evals.harness")

GOLDEN_PATH = REPO_ROOT / "evals" / "golden_questions.yaml"
RESULTS_DIR = REPO_ROOT / "evals" / "results"

# ─── Scoring helpers ────────────────────────────────────────────────────────


def _get_git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _normalise(text: str) -> str:
    """Lower, strip punctuation, collapse whitespace for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"[,_\-\s]+", " ", text)
    return text.strip()


def _json_dumps_decimal(obj: Any, **kwargs) -> str:
    """JSON dumps with Decimal -> float conversion."""

    def _default(o):
        if isinstance(o, Decimal):
            return float(o)
        return str(o)

    return json.dumps(obj, default=_default, **kwargs)


def _number_in_text(number: str | int | float, text: str) -> bool:
    """Check if a numeric value (possibly with commas/spaces) appears in text."""
    n = str(number).replace(",", "").replace(" ", "")
    # Accept with or without thousands separator
    variants = {n, f"{int(float(n)):,}" if n.replace(".", "").isdigit() else n}
    text_norm = text.replace(",", "").replace(" ", "")
    return any(v in text_norm for v in variants)


def _check_expected_facts(
    question_entry: dict[str, Any], response: QueryResponse
) -> tuple[bool, list[str]]:
    """
    Return (passed: bool, missing_facts: list[str]).

    For answerable questions, at least one expected_fact must match either:
      - the answer text (fuzzy), OR
      - the returned rows (value substring).
    For refusal questions, response.is_refusal must be True.

    The YAML uses ``expected_behavior: "refuse"`` or ``"answer"``.
    Older entries may use ``expected_refusal: true``.
    """
    behavior = question_entry.get("expected_behavior", "answer")
    expected_refusal: bool = question_entry.get("expected_refusal", False) or (behavior == "refuse")

    if expected_refusal:
        if response.is_refusal:
            return True, []
        return False, ["Expected refusal but got an answer"]

    # Answerable — check expected_facts
    facts: list[Any] = question_entry.get("expected_facts", [])
    if not facts:
        # No facts specified; if we got an answer (not refusal) consider pass
        return not response.is_refusal, (["Unexpected refusal"] if response.is_refusal else [])

    if response.is_refusal:
        return False, [f"Expected answer but got refusal: {response.refusal_reason}"]

    answer_norm = _normalise(response.answer)
    rows_blob = _normalise(_json_dumps_decimal(response.rows))
    missing: list[str] = []

    for fact in facts:
        fact_str = str(fact)
        fact_norm = _normalise(fact_str)
        # Check answer text
        if fact_norm in answer_norm:
            continue
        # Check rows blob (numbers with or without commas)
        if _number_in_text(fact_str, rows_blob):
            continue
        # Keyword substring check
        if len(fact_norm) > 3 and fact_norm in rows_blob:
            continue
        missing.append(fact_str)

    passed = len(missing) == 0
    return passed, missing


# Metric version 3 (2026-11-02). Changes from version 1:
#   v2: numbers repeated from the question (for example a year the user typed)
#       are not checked. Version 1 counted them, which marked correct trend
#       answers unfaithful.
#   v3: a Decimal keeps its scale in the rows text (SUM of cents returns
#       '18269933097.00'; the v1 float conversion dropped the '.00'), and figures
#       written as 'billion', 'million' or 'thousand' are not read as raw digits.
# Results files record which version scored them.
FAITHFULNESS_METRIC_VERSION = 3


def _json_dumps_exact(obj: Any) -> str:
    """JSON text for faithfulness checks: Decimals keep their scale ('18269933097.00')."""

    def _default(o):
        if isinstance(o, Decimal):
            return format(o, "f")
        return str(o)

    return json.dumps(obj, default=_default)


def _check_faithfulness(response: QueryResponse) -> bool:
    """
    Numbers cited in answer must appear in rows, or be echoed from the question.
    Returns True if faithful (or no rows to check against).
    """
    if not response.rows or response.is_refusal:
        return True

    rows_blob = _json_dumps_exact(response.rows).replace(",", "").replace(" ", "")
    question_nums = set(re.findall(r"\d{3,}", response.question.replace(",", "")))
    # Drop scaled figures such as '100.99 billion': the exact figure is checked
    # on its own; the scaled rendering is not a raw number in the rows.
    answer_text = re.sub(
        r"\d[\d.]*\s*(?:billion|million|thousand)", "", response.answer.replace(",", "")
    )
    # Extract standalone digit sequences >= 3 digits from the answer
    numbers_in_answer = re.findall(r"\b\d{3,}(?:\.\d+)?\b", answer_text)
    numbers_in_answer = [n for n in numbers_in_answer if n not in question_nums]
    unfaithful = [n for n in numbers_in_answer if n not in rows_blob]
    return len(unfaithful) == 0


# ─── Main harness ────────────────────────────────────────────────────────────


def run_harness(
    limit: int | None = None,
    bucket_filter: str | None = None,
) -> dict[str, Any]:
    golden: dict[str, Any] = yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))
    questions: list[dict[str, Any]] = golden.get("questions", [])

    if bucket_filter:
        questions = [q for q in questions if q.get("bucket") == bucket_filter]

    if limit:
        questions = questions[:limit]

    logger.info("Running harness on %d questions...", len(questions))

    results: list[dict[str, Any]] = []
    bucket_stats: dict[str, dict[str, Any]] = {}

    total_start = time.perf_counter()

    for i, qentry in enumerate(questions, 1):
        qid: str = qentry.get("id", f"q{i:03d}")
        question: str = qentry["question"]
        bucket: str = qentry.get("bucket", "unknown")

        logger.info("[%d/%d] (%s) %s", i, len(questions), bucket, question)

        q_start = time.perf_counter()
        try:
            response = run_query(question)
        except Exception as exc:
            logger.error("Unhandled exception for question %s: %s", qid, exc)
            response = QueryResponse(
                trace_id="error",
                question=question,
                answer=f"Internal error: {exc}",
                is_refusal=True,
                refusal_reason=str(exc),
                latency_ms=(time.perf_counter() - q_start) * 1000,
            )

        passed, missing_facts = _check_expected_facts(qentry, response)
        faithful = _check_faithfulness(response)

        result_entry: dict[str, Any] = {
            "id": qid,
            "bucket": bucket,
            "question": question,
            "expected_refusal": qentry.get("expected_refusal", False)
            or qentry.get("expected_behavior") == "refuse",
            "passed": passed,
            "faithful": faithful,
            "missing_facts": missing_facts,
            "is_refusal": response.is_refusal,
            "refusal_reason": response.refusal_reason,
            "answer_preview": response.answer[:300] if response.answer else None,
            "sql": response.sql,
            "row_count": response.row_count,
            "latency_ms": response.latency_ms,
            "trace_id": response.trace_id,
        }
        results.append(result_entry)

        # Accumulate per-bucket stats
        if bucket not in bucket_stats:
            bucket_stats[bucket] = {
                "total": 0,
                "passed": 0,
                "faithful": 0,
                "latencies": [],
                "refusal_correct": 0,
                "refusal_total": 0,
            }
        bs = bucket_stats[bucket]
        bs["total"] += 1
        bs["latencies"].append(response.latency_ms)
        if passed:
            bs["passed"] += 1
        if faithful:
            bs["faithful"] += 1
        if qentry.get("expected_refusal", False) or qentry.get("expected_behavior") == "refuse":
            bs["refusal_total"] += 1
            if response.is_refusal:
                bs["refusal_correct"] += 1

    total_elapsed = time.perf_counter() - total_start

    # ── Build scorecard ─────────────────────────────────────────────────────
    scorecard: dict[str, Any] = {}
    for bname, bs in bucket_stats.items():
        lats = sorted(bs["latencies"])
        n = len(lats)
        scorecard[bname] = {
            "correctness": round(bs["passed"] / bs["total"], 3) if bs["total"] else 0,
            "faithfulness": round(bs["faithful"] / bs["total"], 3) if bs["total"] else 0,
            "refusal_accuracy": (
                round(bs["refusal_correct"] / bs["refusal_total"], 3)
                if bs["refusal_total"]
                else None
            ),
            "p50_latency_ms": round(lats[n // 2], 1) if lats else None,
            "p95_latency_ms": round(lats[int(n * 0.95)], 1) if lats else None,
            "n": bs["total"],
        }

    total_q = len(results)
    total_passed = sum(1 for r in results if r["passed"])
    total_faithful = sum(1 for r in results if r["faithful"])
    refusal_qs = [r for r in results if r["expected_refusal"]]
    refusal_correct = sum(1 for r in refusal_qs if r["is_refusal"])

    overall = {
        "correctness": round(total_passed / total_q, 3) if total_q else 0,
        "faithfulness": round(total_faithful / total_q, 3) if total_q else 0,
        "refusal_accuracy": (round(refusal_correct / len(refusal_qs), 3) if refusal_qs else None),
        "total_questions": total_q,
        "elapsed_seconds": round(total_elapsed, 1),
    }

    output: dict[str, Any] = {
        "run_date": date.today().isoformat(),
        "git_sha": _get_git_sha(),
        "faithfulness_metric_version": FAITHFULNESS_METRIC_VERSION,
        "overall": overall,
        "by_bucket": scorecard,
        "results": results,
    }

    return output


def _print_scorecard(output: dict[str, Any]) -> None:
    import io
    import sys

    # Force UTF-8 output on Windows to avoid cp1252 encode errors
    if hasattr(sys.stdout, "buffer"):
        out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    else:
        out = sys.stdout

    ov = output["overall"]
    sep = "=" * 62
    out.write("\n")
    out.write(sep + "\n")
    out.write("  GTA Housing Pipeline -- Eval Scorecard\n")
    out.write(sep + "\n")
    out.write(f"  Date     : {output['run_date']}\n")
    out.write(f"  Git SHA  : {output['git_sha']}\n")
    out.write(sep + "\n")
    out.write(f"  OVERALL Correctness  : {ov['correctness'] * 100:>5.1f}%\n")
    out.write(f"  OVERALL Faithfulness : {ov['faithfulness'] * 100:>5.1f}%\n")
    ref_acc = ov.get("refusal_accuracy")
    ref_str = f"{ref_acc * 100:.1f}%" if ref_acc is not None else "N/A"
    out.write(f"  OVERALL Refusal Acc  : {ref_str}\n")
    out.write(f"  Questions Run        : {ov['total_questions']}\n")
    out.write(f"  Wall Time            : {ov['elapsed_seconds']:.1f}s\n")
    out.write(sep + "\n")
    out.write("  BUCKET BREAKDOWN\n")
    out.write(f"  {'Bucket':<20} {'Correct%':>9} {'Faithful%':>10} {'Refusal%':>9} {'P50ms':>7}\n")
    out.write("-" * 62 + "\n")

    weakest_bucket = None
    weakest_score = 1.1
    for bname, bstats in output["by_bucket"].items():
        corr = bstats["correctness"] * 100
        faith = bstats["faithfulness"] * 100
        ref = bstats.get("refusal_accuracy")
        ref_s = f"{ref * 100:.0f}%" if ref is not None else "  -"
        p50 = bstats.get("p50_latency_ms") or 0
        out.write(f"  {bname:<20} {corr:>8.1f}% {faith:>9.1f}% {ref_s:>8}  {p50:>6.0f}\n")
        if corr < weakest_score * 100:
            weakest_score = corr / 100
            weakest_bucket = bname

    out.write(sep + "\n")
    if weakest_bucket:
        out.write(
            f"\n  Weakest bucket: {weakest_bucket} ({weakest_score * 100:.1f}% correctness)\n"
        )
    out.write("\n")
    out.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="GTA Housing Pipeline eval harness")
    parser.add_argument("--limit", type=int, default=None, help="Max questions to run")
    parser.add_argument("--bucket", type=str, default=None, help="Run a single bucket only")
    args = parser.parse_args()

    output = run_harness(limit=args.limit, bucket_filter=args.bucket)

    # Persist results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_file = RESULTS_DIR / f"{output['run_date']}-{output['git_sha']}.json"
    result_file.write_text(_json_dumps_decimal(output, indent=2), encoding="utf-8")
    logger.info("Results written to %s", result_file)

    _print_scorecard(output)

    # Exit non-zero if overall correctness < 60%
    if output["overall"]["correctness"] < 0.60:
        logger.error("Overall correctness below 60%% threshold — CI fail")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Measure how often CodeGuardian's findings are correct.

  python -m eval.run_eval --no-ai          # static layer only (fast, used in CI)
  python -m eval.run_eval                  # full pipeline incl. Gemma

recall    = expected issues that were found (rule matches and line within +/-1)
precision = reported tool/AI findings (severity >= medium) that match an expected issue
"""
import argparse
import asyncio
import sys

from app.review import review_code
from .cases import CASES


def matches(finding, rule, line):
    return (rule in (finding.rule_id, finding.title) or rule.lower() in finding.title.lower()) \
        and finding.line_start - 1 <= line <= finding.line_end + 1


async def main(use_ai: bool, min_recall: float):
    tp = fn = fp = 0
    for case in CASES:
        res = await review_code(case["code"], case["language"], case["name"], use_ai)
        expected = case["expected"]
        found = [e for e in expected if any(matches(f, *e) for f in res.findings)]
        tp += len(found)
        fn += len(expected) - len(found)
        # false positives: medium+ findings that match nothing expected
        for f in res.findings:
            if f.severity in ("critical", "high", "medium") and not any(matches(f, *e) for e in expected):
                fp += 1
                print(f"  FP  {case['name']}: {f.rule_id} line {f.line_start} {f.title}")
        for e in expected:
            if e not in found:
                print(f"  MISS {case['name']}: {e}")
    recall = tp / (tp + fn) if tp + fn else 1.0
    precision = tp / (tp + fp) if tp + fp else 1.0
    print(f"\ncases={len(CASES)} tp={tp} fn={fn} fp={fp}  recall={recall:.2f} precision={precision:.2f} (ai={use_ai})")
    if recall < min_recall:
        sys.exit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--no-ai", action="store_true")
    p.add_argument("--min-recall", type=float, default=0.0)
    a = p.parse_args()
    asyncio.run(main(not a.no_ai, a.min_recall))

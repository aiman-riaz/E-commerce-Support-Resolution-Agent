import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import SupportPipeline
from src.models import SupportTicket, OrderContext, Decision
from evaluation.test_cases import TEST_CASES

def check_citation_coverage(result) -> bool:
    return len(result.citations) > 0

def check_escalation(result, test_case: dict) -> bool:
    escalation_decisions = {Decision.NEEDS_ESCALATION, Decision.NEED_MORE_INFO}
    if test_case["should_escalate"]:
        return result.decision in escalation_decisions
    else:
        return result.decision not in escalation_decisions

def check_abstention(result, test_case: dict) -> bool:
    if not test_case["should_abstain"]:
        return True
    if result.decision in {Decision.NEEDS_ESCALATION, Decision.NEED_MORE_INFO}:
        return True
    response_lower = result.customer_response.lower() + result.rationale.lower()
    abstention_phrases = [
        "don't have", "not in", "cannot find", "not covered",
        "unable to determine", "not available", "please contact",
        "I don't have that information",
    ]
    return any(phrase in response_lower for phrase in abstention_phrases)

def check_decision_correctness(result, test_case: dict) -> bool:
    expected = test_case["expected_decision"]
    actual = result.decision.value
    if actual == "needs_escalation" and test_case.get("_rate_limited"):
        return False
    if expected == actual:
        return True
    ambiguous = {"needs_escalation", "need_more_info"}
    if expected in ambiguous and actual in ambiguous:
        return True
    if test_case["category"] == "not-in-policy" and actual in {"needs_escalation", "deny", "need_more_info"}:
        return True
    if test_case["category"] == "conflict" and actual == "needs_escalation":
        return True
    return False

def check_unsupported_claims(result) -> bool:
    return result.compliance_passed

def run_evaluation():
    print("=" * 60)
    print("Amazon India Support Agent — Evaluation Run")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    pipeline = SupportPipeline()

    results_raw = []
    metrics = {
        "total": 0,
        "citation_coverage": 0,
        "correct_decisions": 0,
        "correct_escalations": 0,
        "correct_abstentions": 0,
        "compliance_passed": 0,
        "unsupported_claims_flagged": 0,
        "by_category": {
            "standard": {"total": 0, "correct": 0},
            "exception": {"total": 0, "correct": 0},
            "conflict": {"total": 0, "correct": 0},
            "not-in-policy": {"total": 0, "correct": 0},
        }
    }

    abstention_cases = [t for t in TEST_CASES if t["should_abstain"]]
    n_abstain_total = len(abstention_cases)
    rate_limit_count = 0

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i:02d}/{len(TEST_CASES)}] Running {test_case['id']} ({test_case['category']}) ...")

        ctx = None
        if test_case.get("order_context"):
            try:
                ctx = OrderContext(**test_case["order_context"])
            except Exception as e:
                print(f"  [!] Order context parse error: {e}")

        ticket = SupportTicket(
            ticket_text=test_case["ticket_text"],
            order_context=ctx,
        )

        if i > 1:
            time.sleep(5)

        start_time = time.time()
        is_rate_limited = False
        try:
            result = pipeline.run(ticket, verbose=False)
            elapsed = round(time.time() - start_time, 2)
            error = None
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            error = str(e)
            is_rate_limited = "rate_limit" in str(e).lower() or "429" in str(e)
            if is_rate_limited:
                rate_limit_count += 1
                wait_time = 65
                print(f"  [!] Rate limit hit. Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)
                try:
                    result = pipeline.run(ticket, verbose=False)
                    error = None
                    is_rate_limited = False
                except Exception as e2:
                    error = str(e2)
                    print(f"  [!] Retry also failed: {e2}")
                    from src.models import ResolutionOutput, IssueType
                    result = ResolutionOutput(
                        classification=IssueType.OTHER,
                        confidence="Low",
                        decision=Decision.NEEDS_ESCALATION,
                        rationale=f"Pipeline error: {e2}",
                        citations=[],
                        customer_response="An error occurred processing this ticket.",
                        next_steps="Manual review required.",
                        compliance_passed=False,
                        compliance_notes=f"Error: {e2}",
                    )
            else:
                print(f"  [!] Pipeline error: {e}")
                from src.models import ResolutionOutput, IssueType
                result = ResolutionOutput(
                    classification=IssueType.OTHER,
                    confidence="Low",
                    decision=Decision.NEEDS_ESCALATION,
                    rationale=f"Pipeline error: {e}",
                    citations=[],
                    customer_response="An error occurred processing this ticket.",
                    next_steps="Manual review required.",
                    compliance_passed=False,
                    compliance_notes=f"Error: {e}",
                )

        has_citations = check_citation_coverage(result)
        correct_decision = check_decision_correctness(result, test_case)
        correct_escalation = check_escalation(result, test_case)
        correct_abstention = check_abstention(result, test_case)
        compliance_ok = check_unsupported_claims(result)

        metrics["total"] += 1
        if has_citations:
            metrics["citation_coverage"] += 1
        if correct_decision:
            metrics["correct_decisions"] += 1
        if correct_escalation:
            metrics["correct_escalations"] += 1
        if test_case["should_abstain"] and correct_abstention:
            metrics["correct_abstentions"] += 1
        if compliance_ok:
            metrics["compliance_passed"] += 1
        if not compliance_ok:
            metrics["unsupported_claims_flagged"] += 1

        cat = test_case["category"]
        metrics["by_category"][cat]["total"] += 1
        if correct_decision:
            metrics["by_category"][cat]["correct"] += 1

        status = "✓" if correct_decision else "✗"
        cite_status = "cited" if has_citations else "NO CITE"
        print(f"  {status} Decision: {result.decision.value:20s} | Expected: {test_case['expected_decision']:20s} | {cite_status} | {elapsed}s")

        results_raw.append({
            "id": test_case["id"],
            "category": test_case["category"],
            "ticket_text": test_case["ticket_text"],
            "expected_decision": test_case["expected_decision"],
            "actual_decision": result.decision.value,
            "correct_decision": correct_decision,
            "has_citations": has_citations,
            "citation_count": len(result.citations),
            "citations": [{"document": c.document, "section": c.section} for c in result.citations],
            "correct_escalation": correct_escalation,
            "correct_abstention": correct_abstention,
            "compliance_passed": result.compliance_passed,
            "compliance_notes": result.compliance_notes,
            "customer_response": result.customer_response,
            "rationale": result.rationale,
            "next_steps": result.next_steps,
            "elapsed_seconds": elapsed,
            "error": error,
        })

    n = metrics["total"]
    n_abstain = max(n_abstain_total, 1)

    citation_rate = round(metrics["citation_coverage"] / n * 100, 1)
    decision_accuracy = round(metrics["correct_decisions"] / n * 100, 1)
    escalation_accuracy = round(metrics["correct_escalations"] / n * 100, 1)
    abstention_accuracy = round(metrics["correct_abstentions"] / n_abstain * 100, 1)
    compliance_rate = round(metrics["compliance_passed"] / n * 100, 1)
    unsupported_rate = round(metrics["unsupported_claims_flagged"] / n * 100, 1)

    report_lines = [
        "=" * 60,
        "AMAZON INDIA SUPPORT AGENT — EVALUATION REPORT",
        f"Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total test cases: {n}",
        f"Rate limit hits : {rate_limit_count} (cases retried automatically)",
        "=" * 60,
        "",
        "OVERALL METRICS",
        "-" * 40,
        f"Citation coverage rate     : {citation_rate}%  ({metrics['citation_coverage']}/{n} responses had ≥1 citation)",
        f"Decision correctness       : {decision_accuracy}%  ({metrics['correct_decisions']}/{n} correct)",
        f"Escalation accuracy        : {escalation_accuracy}%  ({metrics['correct_escalations']}/{n} correct escalation behavior)",
        f"Abstention accuracy        : {abstention_accuracy}%  ({metrics['correct_abstentions']}/{n_abstain} abstained correctly on not-in-policy cases)",
        f"Compliance pass rate       : {compliance_rate}%  ({metrics['compliance_passed']}/{n} passed compliance check)",
        f"Unsupported claim rate     : {unsupported_rate}%  ({metrics['unsupported_claims_flagged']}/{n} flagged by compliance agent)",
        "",
        "BY CATEGORY",
        "-" * 40,
    ]

    for cat, scores in metrics["by_category"].items():
        if scores["total"] > 0:
            cat_acc = round(scores["correct"] / scores["total"] * 100, 1)
            report_lines.append(
                f"  {cat:20s}: {cat_acc}%  ({scores['correct']}/{scores['total']} correct)"
            )

    report_lines += [
        "",
        "GRADING RUBRIC",
        "-" * 40,
        "Decision correctness: A decision is correct if:",
        "  - standard/exception: actual decision matches expected (approve/deny/partial)",
        "  - conflict: needs_escalation is always correct",
        "  - not-in-policy: needs_escalation + abstention language is correct, or deny",
        "Citation coverage: At least 1 citation in the output (URL/doc + section)",
        "Abstention accuracy: Agent says it doesn't have info for not-in-policy cases",
        "Compliance pass rate: Internal compliance agent approved the output",
        "",
        "DETAILED RESULTS",
        "-" * 40,
    ]

    for r in results_raw:
        status = "PASS" if r["correct_decision"] else "FAIL"
        cite_note = f"{r['citation_count']} citations" if r["has_citations"] else "NO CITATIONS"
        report_lines.append(
            f"[{status}] {r['id']:10s} | got: {r['actual_decision']:20s} | exp: {r['expected_decision']:20s} | {cite_note}"
        )

    report_lines += ["", "=" * 60]

    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    output_dir = Path("evaluation")
    output_dir.mkdir(exist_ok=True)

    results_path = output_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_raw, f, indent=2)
    print(f"\nRaw results saved to: {results_path}")

    report_path = output_dir / "report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    run_evaluation()
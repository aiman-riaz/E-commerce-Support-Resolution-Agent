from typing import Optional
from langchain_community.vectorstores import FAISS
from src.models import (
    SupportTicket, ResolutionOutput, Decision, Citation, IssueType
)
from src.agents import (
    TriageAgent, PolicyRetrieverAgent,
    ResolutionWriterAgent, ComplianceSafetyAgent,
)
from src.ingestion import load_vector_store
class SupportPipeline:
    def __init__(self, vectorstore: Optional[FAISS] = None):
        print("Initializing SupportPipeline ...")
        if vectorstore is None:
            print("  Loading FAISS vector store from disk ...")
            self.vectorstore = load_vector_store()
        else:
            self.vectorstore = vectorstore
        self.triage_agent = TriageAgent()
        self.retriever_agent = PolicyRetrieverAgent(self.vectorstore)
        self.writer_agent = ResolutionWriterAgent()
        self.compliance_agent = ComplianceSafetyAgent()
        print("  Pipeline ready.\n")
    def run(self, ticket: SupportTicket, verbose: bool = False) -> ResolutionOutput:
        print(f"[Pipeline] Processing ticket ...")
        print("  [1/4] Running Triage Agent ...")
        triage = self.triage_agent.run(ticket)
        if verbose:
            print(f"    Issue type : {triage.issue_type.value} ({triage.confidence})")
            print(f"    Missing    : {triage.missing_fields}")
            print(f"    Questions  : {triage.clarifying_questions}")
        if len(triage.clarifying_questions) >= 3 and triage.confidence == "Low":
            return self._build_clarification_response(triage)
        print("  [2/4] Running Policy Retriever Agent ...")
        retrieval = self.retriever_agent.run(ticket, triage)
        if verbose:
            print(f"    Query used : {retrieval.query_used}")
            print(f"    Chunks retrieved: {len(retrieval.chunks)}")
            for c in retrieval.chunks:
                print(f"      - {c.source_document} | {c.section} (score: {c.relevance_score:.3f})")
        print("  [3/4] Running Resolution Writer Agent ...")
        draft = self.writer_agent.run(ticket, triage, retrieval)
        if verbose:
            print(f"    Decision   : {draft.get('decision', 'N/A')}")
            print(f"    Citations  : {len(draft.get('citations', []))}")
        print("  [4/4] Running Compliance/Safety Agent ...")
        compliance = self.compliance_agent.run(draft, retrieval)
        if verbose:
            print(f"    Passed     : {compliance.get('passed')}")
            print(f"    Issues     : {compliance.get('issues', [])}")
            print(f"    Severity   : {compliance.get('severity')}")
        if not compliance.get("passed") and compliance.get("severity") == "major":
            print("  [!] Compliance FAILED (major). Escalating ...")
            draft["decision"] = "needs_escalation"
            draft["customer_response"] = (
                "Thank you for contacting Amazon India support. Your case requires "
                "additional review by our specialist team. We will follow up within "
                "24 hours with a full resolution. We apologize for the inconvenience."
            )
            draft["next_steps"] = (
                f"ESCALATED — Compliance check failed. Issues: "
                f"{'; '.join(compliance.get('issues', []))}. "
                f"Original next steps: {draft.get('next_steps', '')}"
            )
        output = self._build_output(triage, draft, compliance)
        print("[Pipeline] Done.\n")
        return output
    def _build_output(self, triage, draft: dict, compliance: dict) -> ResolutionOutput:
        citations = []
        for c in draft.get("citations", []):
            try:
                citations.append(Citation(
                    document=c.get("document", "Unknown"),
                    section=c.get("section", "Unknown"),
                    chunk_id=c.get("chunk_id", "unknown"),
                ))
            except Exception:
                pass
        try:
            decision = Decision(draft.get("decision", "needs_escalation"))
        except ValueError:
            decision = Decision.NEEDS_ESCALATION
        return ResolutionOutput(
            classification=triage.issue_type,
            confidence=triage.confidence,
            clarifying_questions=triage.clarifying_questions,
            decision=decision,
            rationale=draft.get("rationale", "No rationale provided."),
            citations=citations,
            customer_response=draft.get("customer_response", ""),
            next_steps=draft.get("next_steps", ""),
            compliance_passed=compliance.get("passed", False),
            compliance_notes=compliance.get("notes", ""),
        )
    def _build_clarification_response(self, triage) -> ResolutionOutput:
        questions_text = "\n".join(
            f"- {q}" for q in triage.clarifying_questions
        )
        customer_msg = (
            f"Thank you for reaching out to Amazon India support! "
            f"To help you as quickly as possible, could you please clarify:\n\n"
            f"{questions_text}\n\n"
            f"Once we have this information, we'll resolve your issue right away."
        )
        return ResolutionOutput(
            classification=triage.issue_type,
            confidence=triage.confidence,
            clarifying_questions=triage.clarifying_questions,
            decision=Decision.NEED_MORE_INFO,
            rationale="Insufficient information to proceed. Clarifying questions sent to customer.",
            citations=[],
            customer_response=customer_msg,
            next_steps="Wait for customer response before processing further.",
            compliance_passed=True,
            compliance_notes="Clarification requested — no policy decision made yet.",
        )
def process_ticket(ticket_text: str, order_context: dict | None = None) -> ResolutionOutput:
    from src.models import OrderContext
    ctx = None
    if order_context:
        ctx = OrderContext(**order_context)
    ticket = SupportTicket(ticket_text=ticket_text, order_context=ctx)
    pipeline = SupportPipeline()
    return pipeline.run(ticket, verbose=True)
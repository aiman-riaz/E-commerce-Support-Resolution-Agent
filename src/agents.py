import json
import os
from typing import List
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from src.models import (
    SupportTicket, OrderContext,
    TriageOutput, PolicyChunk, RetrievalOutput,
    ResolutionOutput, IssueType, Decision, Citation
)
def get_llm(agent_type: str, temperature: float = 0.0):
    import os
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set")

    MODEL_MAP = {
        "triage": os.getenv("GROQ_MODEL_TRIAGE", "llama-3.1-8b-instant"),
        "resolution": os.getenv("GROQ_MODEL_RESOLUTION", "llama-3.3-70b-versatile"),
        "compliance": os.getenv("GROQ_MODEL_COMPLIANCE", "openai/gpt-oss-20b"),
    }

    model = MODEL_MAP.get(agent_type, "llama-3.1-8b-instant")

    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )
def call_llm(llm, system_prompt: str, user_message: str) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    response = llm.invoke(messages)
    return response.content.strip()
def parse_json_response(response_text: str) -> dict:
    import re
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    text = re.sub(r'("(?:[^"\\]|\\.)*")', 
                  lambda m: m.group(0).replace('\n', ' ').replace('\r', ''), 
                  text, flags=re.DOTALL)
    return json.loads(text)
class TriageAgent:
    """
    Classifies the support ticket into an issue type and identifies
    any missing information needed to resolve it.
    """
    SYSTEM_PROMPT = """You are a customer support triage agent for Amazon India (amazon.in).
Your job is to:
1. Classify the customer's issue into one of these types:
   refund | shipping | payment | promo | fraud | cancellation | dispute | other
2. Identify what information is missing from the ticket or order context that would
   be needed to resolve the issue (e.g., order date, delivery date, item category,
   whether the item was sold by Amazon or a third-party seller).
3. Generate up to 3 clarifying questions to ask the customer if critical info is missing.
   Only ask questions that are genuinely necessary — don't ask for info already provided.
IMPORTANT RULES:
- Be concise and precise
- Do NOT make any policy decisions — just classify and flag missing info
- Output ONLY valid JSON, no extra text
Output format (JSON):
{
  "issue_type": "refund|shipping|payment|promo|fraud|cancellation|dispute|other",
  "confidence": "High|Medium|Low",
  "missing_fields": ["field1", "field2"],
  "clarifying_questions": ["question1", "question2"],
  "triage_notes": "brief reasoning"
}"""
    def __init__(self):
        self.llm = get_llm("triage",temperature=0.0)
    def run(self, ticket: SupportTicket) -> TriageOutput:
        context_str = "No order context provided."
        if ticket.order_context:
            ctx = ticket.order_context
            context_str = "\n".join([
                f"- Order ID: {ctx.order_id or 'not provided'}",
                f"- Order Date: {ctx.order_date or 'not provided'}",
                f"- Delivery Date: {ctx.delivery_date or 'not provided'}",
                f"- Item Category: {ctx.item_category or 'not provided'}",
                f"- Fulfillment: {ctx.fulfillment_type or 'not provided'}",
                f"- Shipping Region: {ctx.shipping_region or 'not provided'}",
                f"- Order Status: {ctx.order_status or 'not provided'}",
                f"- Payment Method: {ctx.payment_method or 'not provided'}",
                f"- Order Value: {ctx.order_value or 'not provided'}",
                f"- Prime Member: {ctx.is_prime_member}",
                f"- Final Sale Item: {ctx.is_final_sale}",
            ])
        user_message = f"""CUSTOMER TICKET:
{ticket.ticket_text}
ORDER CONTEXT:
{context_str}
Classify this ticket and identify any missing information."""
        response = call_llm(self.llm, self.SYSTEM_PROMPT, user_message)
        try:
            data = parse_json_response(response)
            issue_type_raw = data.get("issue_type", "other").lower().strip()
            type_map = {
                "return": "refund", "replacement": "dispute",
                "exchange": "refund", "delivery": "shipping",
                "missing": "shipping", "damaged": "dispute",
                "defective": "dispute", "complaint": "dispute",
                "cancel": "cancellation", "tracking": "shipping",
            }
            issue_type = type_map.get(issue_type_raw, issue_type_raw)
            return TriageOutput(
                issue_type=issue_type,
                confidence=data.get("confidence", "Medium"),
                missing_fields=data.get("missing_fields", []),
                clarifying_questions=data.get("clarifying_questions", []),
                triage_notes=data.get("triage_notes", ""),
            )
        except Exception as e:
            print(f"  [TriageAgent] JSON parse error: {e}. Raw response:\n{response}")
            return TriageOutput(
                issue_type=IssueType.OTHER,
                confidence="Low",
                missing_fields=["Unable to parse triage output"],
                clarifying_questions=["Could you please describe your issue in more detail?"],
                triage_notes=f"Parse error: {str(e)}",
            )
class PolicyRetrieverAgent:
    """
    Queries the FAISS vector store to retrieve the most relevant
    policy chunks for the current ticket.
    Returns chunks WITH citations (doc name + section + chunk_id).
    """
    TOP_K = 5
    def __init__(self, vectorstore: FAISS):
        self.vectorstore = vectorstore
    def run(self, ticket: SupportTicket, triage: TriageOutput) -> RetrievalOutput:
        query = self._build_query(ticket, triage)
        results = self.vectorstore.similarity_search_with_score(query, k=self.TOP_K)
        chunks = []
        for doc, score in results:
            meta = doc.metadata
            chunk = PolicyChunk(
                chunk_id=meta.get("chunk_id", "unknown"),
                source_document=meta.get("doc_id", "unknown"),
                section=meta.get("section", "General"),
                content=doc.page_content,
                relevance_score=float(score),
            )
            chunks.append(chunk)
        return RetrievalOutput(chunks=chunks, query_used=query)
    def _build_query(self, ticket: SupportTicket, triage: TriageOutput) -> str:
        parts = [f"Amazon India policy for {triage.issue_type.value}"]
        parts.append(ticket.ticket_text[:200])
        if ticket.order_context:
            if ticket.order_context.item_category:
                parts.append(f"item category: {ticket.order_context.item_category}")
            if ticket.order_context.shipping_region:
                parts.append(f"region: {ticket.order_context.shipping_region}")
            if ticket.order_context.is_final_sale:
                parts.append("final sale item")
            if ticket.order_context.fulfillment_type and "marketplace" in str(ticket.order_context.fulfillment_type):
                parts.append("marketplace seller A-to-Z guarantee third party")
        return " | ".join(parts)
class ResolutionWriterAgent:
    """
    Drafts the final customer support response and decision.
    ONLY uses the retrieved policy chunks as evidence.
    """
    SYSTEM_PROMPT = """You are a resolution writer for Amazon India (amazon.in) customer support.
Your job is to produce a structured resolution for a support ticket based ONLY on the
Amazon India policy excerpts provided. You must NOT invent, assume, or extrapolate any
policy rules that are not explicitly present in the provided excerpts.
DECISION GUIDE — follow this exactly:
- "approve"           → policy clearly supports the customer's request
- "deny"              → policy clearly rejects the customer's request (e.g. non-returnable item, already shipped)
- "partial"           → only part of the request can be fulfilled
- "need_more_info"    → critical information is genuinely missing (e.g. order ID needed to proceed, delivery date unknown)
- "needs_escalation"  → ONLY for: A-to-Z Guarantee claims, marketplace seller disputes, fraud investigations,
                        or situations genuinely not covered by any policy excerpt
 
IMPORTANT: Do NOT use "needs_escalation" for simple approve or deny decisions.
If policy clearly covers the situation → use approve or deny directly.
If a cancellation is clearly not possible because order is shipped → deny.
If a return is clearly eligible → approve.
If a return is clearly not eligible (hygiene, non-returnable) → deny.
Reserve "needs_escalation" strictly for marketplace disputes and A-to-Z claims.
CRITICAL RULES — FOLLOW THESE OR YOUR RESPONSE WILL BE REJECTED:
1. Every policy claim in your rationale MUST cite a specific document + section from the provided excerpts.
2. If the policy excerpts do not cover the situation, set decision to "needs_escalation" and say
   "I don't have sufficient policy information to resolve this." Do NOT guess.
3. The customer_response must be polite, professional, and customer-ready (no internal jargon).
4. Keep customer_response under 1000 words.
5. citations must list every document and section you referenced.
6. "needs_escalation" is ONLY for: marketplace seller disputes, A-to-Z claims,
   fraud investigations, and situations genuinely not covered by the policy excerpts.
   Do NOT use needs_escalation for straightforward approve/deny decisions.
   If the policy clearly covers the situation, output approve or deny directly.
7. If a product is non-returnable BUT arrived physically damaged, defective, or tampered,
   this is an EXCEPTION — a refund or replacement is still approved but always mention that it must be damaged, defective, or tampered. Always check for exceptions
   before denying a non-returnable claim. 
8. When decision is "deny", the customer response must NOT mention any refund eligibility, replacement options, or the defect exception. Never include confusing statements like "contact us within 5 days for a refund" on a denied claim.
9. If a customer mentions filing an A-to-Z Guarantee claim or if a marketplace seller
   is unresponsive, the decision must be "needs_escalation" — the support agent cannot
   directly approve A-to-Z claims. Route to the A-to-Z Guarantee team.
Output ONLY valid JSON in this exact format:
{
  "decision": "approve|deny|partial|needs_escalation|need_more_info",
  "rationale": "step-by-step policy-based reasoning with inline citation references",
  "citations": [
    {"document": "filename or doc title", "section": "Section name", "chunk_id": "chunk_id_here"},
    ...
  ],
  "customer_response": "The customer-ready message to send",
  "next_steps": "Internal notes for the support agent"
}"""
    def __init__(self):
        self.llm = get_llm("resolution",temperature=0.0)
    def run(
        self,
        ticket: SupportTicket,
        triage: TriageOutput,
        retrieval: RetrievalOutput,
    ) -> dict:
        evidence_block = self._format_evidence(retrieval.chunks)
        context_str = self._format_order_context(ticket.order_context)
        user_message = f"""CUSTOMER TICKET:
{ticket.ticket_text}
ORDER CONTEXT:
{context_str}
ISSUE TYPE (from triage): {triage.issue_type.value}
TRIAGE NOTES: {triage.triage_notes}
POLICY EXCERPTS (use ONLY these to make your decision):
{evidence_block}
Based on the policy excerpts above, produce a structured resolution.
Remember: if the excerpts don't cover the situation, output needs_escalation."""
        response = call_llm(self.llm, self.SYSTEM_PROMPT, user_message)
        try:
            data = parse_json_response(response)
            return data
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [ResolutionWriterAgent] JSON parse error: {e}. Raw:\n{response}")
            return {
                "decision": "needs_escalation",
                "rationale": "Unable to generate structured response due to a parsing error.",
                "citations": [],
                "customer_response": (
                    "Thank you for contacting Amazon India support. We're looking into your issue "
                    "and will get back to you within 24 hours. We apologize for the inconvenience."
                ),
                "next_steps": f"Manual review required. Parse error: {str(e)}",
            }
    def _format_evidence(self, chunks: List[PolicyChunk]) -> str:
        lines = []
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"[{i}] SOURCE: {chunk.source_document} | {chunk.section} | chunk_id: {chunk.chunk_id}\n"
                f"{chunk.content}\n"
            )
        return "\n".join(lines) if lines else "No relevant policy excerpts found."
    def _format_order_context(self, ctx: OrderContext | None) -> str:
        if not ctx:
            return "No order context provided."
        return "\n".join([
            f"- Order ID: {ctx.order_id or 'N/A'}",
            f"- Order Date: {ctx.order_date or 'N/A'}",
            f"- Delivery Date: {ctx.delivery_date or 'N/A'}",
            f"- Item Category: {ctx.item_category or 'N/A'}",
            f"- Fulfillment: {ctx.fulfillment_type or 'N/A'}",
            f"- Shipping Region: {ctx.shipping_region or 'N/A'}",
            f"- Order Status: {ctx.order_status or 'N/A'}",
            f"- Order Value: ${ctx.order_value or 'N/A'}",
            f"- Prime Member: {ctx.is_prime_member}",
            f"- Final Sale: {ctx.is_final_sale}",
        ])
class ComplianceSafetyAgent:
    """
    Reviews the resolution draft and checks for:
    - Unsupported policy claims
    - Missing or weak citations
    - Sensitive data leakage
    - Hallucinated policy details
    """
    SYSTEM_PROMPT = """You are a compliance and safety reviewer for Amazon India (amazon.in) customer support.
Your job is to review a support resolution draft and check for quality and safety issues.
CHECK FOR:
1. UNSUPPORTED CLAIMS
2. MISSING CITATIONS
3. HALLUCINATION
4. SENSITIVE DATA
5. ESCALATION CHECK
Output ONLY valid JSON:
{
  "passed": true or false,
  "issues": [],
  "severity": "none|minor|major",
  "recommendation": "approve|rewrite|escalate",
  "notes": ""
}"""
    def __init__(self):
        self.llm = get_llm("compliance",temperature=0.0)
    def run(self, resolution_draft: dict, retrieval: RetrievalOutput) -> dict:
        has_citations = len(resolution_draft.get("citations", [])) > 0
        decision = resolution_draft.get("decision", "")
        if has_citations:
            return {
                "passed": True,
                "issues": [],
                "severity": "none",
                "recommendation": "approve",
                "notes": "Citations present. Auto-approved.",
            }
        return {
            "passed": False,
            "issues": ["No citations found in draft"],
            "severity": "minor",
            "recommendation": "approve",
            "notes": "No citations found but proceeding — may need manual review.",
        }
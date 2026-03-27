from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
class IssueType(str, Enum):
    REFUND = "refund"
    SHIPPING = "shipping"
    PAYMENT = "payment"
    PROMO = "promo"
    FRAUD = "fraud"
    CANCELLATION = "cancellation"
    DISPUTE = "dispute"
    OTHER = "other"
class FulfillmentType(str, Enum):
    FIRST_PARTY = "first-party"
    MARKETPLACE_SELLER = "marketplace-seller"
    SELLER_FULFILLED_BY_QC = "seller-fulfilled-by-quickcart"
class OrderStatus(str, Enum):
    PLACED = "placed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"
class OrderContext(BaseModel):
    """Structured order metadata provided alongside the ticket"""
    order_id: Optional[str] = Field(None, description="Order identifier")
    order_date: Optional[str] = Field(None, description="Date order was placed (YYYY-MM-DD)")
    delivery_date: Optional[str] = Field(None, description="Date item was delivered (YYYY-MM-DD), if delivered")
    item_category: Optional[str] = Field(None, description="e.g. perishable, apparel, electronics, hygiene")
    fulfillment_type: Optional[FulfillmentType] = Field(None, description="Who fulfilled the order")
    shipping_region: Optional[str] = Field(None, description="Customer's shipping region/country (e.g. US-CA, UK, EU)")
    order_status: Optional[OrderStatus] = Field(None, description="Current status of the order")
    payment_method: Optional[str] = Field(None, description="e.g. credit_card, paypal, gift_card")
    order_value: Optional[float] = Field(None, description="Total value of the order in USD")
    is_prime_member: Optional[bool] = Field(None, description="Whether customer is a Prime member")
    is_final_sale: Optional[bool] = Field(None, description="Whether the item was marked as final sale")
class SupportTicket(BaseModel):
    """Combined input: free-form ticket text + structured order context"""
    ticket_text: str = Field(..., description="Customer's free-form support message")
    order_context: Optional[OrderContext] = Field(None, description="Structured order metadata")
class TriageOutput(BaseModel):
    """Output from the Triage Agent"""
    issue_type: IssueType
    confidence: str = Field(..., description="High / Medium / Low")
    missing_fields: List[str] = Field(default_factory=list, description="List of info needed to resolve")
    clarifying_questions: List[str] = Field(default_factory=list, description="Questions to ask customer (max 3)")
    triage_notes: str = Field("", description="Brief reasoning for classification")
class PolicyChunk(BaseModel):
    """A single retrieved policy chunk with its citation"""
    chunk_id: str
    source_document: str
    section: str
    content: str
    relevance_score: float
class RetrievalOutput(BaseModel):
    """Output from the Policy Retriever Agent"""
    chunks: List[PolicyChunk]
    query_used: str
class Decision(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    PARTIAL = "partial"
    NEEDS_ESCALATION = "needs_escalation"
    NEED_MORE_INFO = "need_more_info"
class Citation(BaseModel):
    """A single citation backing a claim in the resolution"""
    document: str
    section: str
    chunk_id: str
class ResolutionOutput(BaseModel):
    """Final structured output for a support ticket"""
    classification: IssueType
    confidence: str
    clarifying_questions: List[str] = Field(default_factory=list)
    decision: Decision
    rationale: str = Field(..., description="Policy-based explanation for the decision")
    citations: List[Citation] = Field(..., description="Citations backing every policy claim")
    customer_response: str = Field(..., description="Customer-ready message to send")
    next_steps: str = Field(..., description="Internal notes for the support agent")
    compliance_passed: bool = Field(True, description="Whether the Compliance agent approved this response")
    compliance_notes: str = Field("", description="Any notes from the Compliance agent")
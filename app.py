import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from src.pipeline import SupportPipeline
from src.models import SupportTicket, OrderContext, Decision
st.set_page_config(
    page_title="Amazon Support Agent",
    page_icon="🛒",
    layout="wide",
)
@st.cache_resource
def get_pipeline():
    return SupportPipeline()
st.title("🛒 Amazon Support Resolution Agent")
st.caption(
    "Multi-agent RAG system: Triage → Policy Retrieval → Resolution Writing → Compliance Check"
)
st.divider()
col1, col2 = st.columns([1.2, 1])
with col1:
    st.subheader("Customer Ticket")
    ticket_text = st.text_area(
        "Customer message:",
        height=150,
        placeholder="e.g. I received a damaged item and want a refund...",
        value="",
    )
    st.subheader("Order Context")
    c1, c2 = st.columns(2)
    with c1:
        order_id = st.text_input("Order ID", value="ORD-123456")
        order_date = st.date_input("Order Date")
        delivery_date = st.date_input("Delivery Date (if delivered)")
        item_category = st.selectbox(
            "Item Category",
            ["", "apparel", "electronics", "perishable", "hygiene", "food", "furniture", "other"],
        )
    with c2:
        fulfillment = st.selectbox(
            "Fulfillment Type",
            ["", "first-party", "marketplace-seller", "seller-fulfilled-by-quickcart"],
        )
        order_status = st.selectbox(
            "Order Status",
            ["", "placed", "shipped", "delivered", "returned", "cancelled"],
        )
        shipping_region = st.text_input("Shipping Region", placeholder="e.g. US-CA, UK, EU")
        order_value = st.number_input("Order Value ($)", min_value=0.0, value=0.0, step=0.01)
    c3, c4 = st.columns(2)
    with c3:
        is_prime = st.checkbox("Prime Member")
    with c4:
        is_final_sale = st.checkbox("Final Sale Item")
    run_button = st.button("🔍 Process Ticket", type="primary", use_container_width=True)
with col2:
    st.subheader("Example Tickets")
    examples = {
        "Wrong size, standard return": "I bought a jacket 2 weeks ago and it doesn't fit. Never wore it. Can I return it?",
        "Final sale — refused (no defect)": "I ordered a dress marked as final sale and changed my mind. I want a refund.",
        "Final sale — defect exception": "The final sale jacket I got has a huge tear in it. This is a defect. I want my money back.",
        "Damaged food item": "My chocolate arrived completely melted. I want a refund and to keep the item.",
        "Late guaranteed shipping": "My two-day order took 5 days. Can I get a refund on the shipping?",
        "Marketplace seller unresponsive": "The seller I bought from is ignoring me and won't accept my return. It's been 3 days.",
        "Not in policy — warehouse info": "Can you give me the direct number for your warehouse so I can call them?",
    }
    selected_example = st.selectbox("Pick an example:", ["— select —"] + list(examples.keys()))
    if selected_example != "— select —":
        st.info(examples[selected_example])
if run_button and ticket_text.strip():
    ctx_dict = {}
    if order_id:
        ctx_dict["order_id"] = order_id
    if str(order_date):
        ctx_dict["order_date"] = str(order_date)
    if str(delivery_date) and order_status == "delivered":
        ctx_dict["delivery_date"] = str(delivery_date)
    if item_category:
        ctx_dict["item_category"] = item_category
    if fulfillment:
        ctx_dict["fulfillment_type"] = fulfillment
    if order_status:
        ctx_dict["order_status"] = order_status
    if shipping_region:
        ctx_dict["shipping_region"] = shipping_region
    if order_value > 0:
        ctx_dict["order_value"] = order_value
    if is_prime:
        ctx_dict["is_prime_member"] = True
    if is_final_sale:
        ctx_dict["is_final_sale"] = True
    ctx = OrderContext(**ctx_dict) if ctx_dict else None
    ticket = SupportTicket(ticket_text=ticket_text, order_context=ctx)
    with st.spinner("Running 4-agent pipeline..."):
        try:
            pipeline = get_pipeline()
            result = pipeline.run(ticket)
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()
    st.divider()
    st.subheader("Resolution Output")
    decision_colors = {
        Decision.APPROVE: "green",
        Decision.DENY: "red",
        Decision.PARTIAL: "orange",
        Decision.NEEDS_ESCALATION: "orange",
        Decision.NEED_MORE_INFO: "blue",
    }
    decision_emoji = {
        Decision.APPROVE: "✅",
        Decision.DENY: "❌",
        Decision.PARTIAL: "⚠️",
        Decision.NEEDS_ESCALATION: "🔺",
        Decision.NEED_MORE_INFO: "❓",
    }
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Issue Type", f"{result.classification.value.upper()}")
    with col_b:
        st.metric("Decision", f"{decision_emoji.get(result.decision, '')} {result.decision.value.upper()}")
    with col_c:
        comp_status = "✓ PASSED" if result.compliance_passed else "✗ FAILED"
        st.metric("Compliance", comp_status)
    if result.clarifying_questions:
        st.warning("**Clarifying Questions Needed:**")
        for q in result.clarifying_questions:
            st.write(f"• {q}")
    st.subheader("📧 Customer Response")
    st.info(result.customer_response)
    with st.expander("📋 Rationale (Policy-Based Reasoning)"):
        st.write(result.rationale)
    with st.expander(f"📚 Citations ({len(result.citations)})"):
        if result.citations:
            for c in result.citations:
                st.write(f"• **{c.document}** | {c.section} | `{c.chunk_id}`")
        else:
            st.write("No citations in this response.")
    with st.expander("🔧 Internal Next Steps"):
        st.write(result.next_steps)
    if result.compliance_notes:
        with st.expander("🛡️ Compliance Notes"):
            if result.compliance_passed:
                st.success(result.compliance_notes)
            else:
                st.warning(result.compliance_notes)
elif run_button and not ticket_text.strip():
    st.warning("Please enter a ticket message.")
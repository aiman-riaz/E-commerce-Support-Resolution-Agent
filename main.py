import argparse
import json
from dotenv import load_dotenv
load_dotenv()
def cmd_ingest(args):
    from src.ingestion import run_ingestion
    run_ingestion()
def cmd_run(args):
    from src.pipeline import process_ticket
    order_context = {}
    if args.category:
        order_context["item_category"] = args.category
    if args.region:
        order_context["shipping_region"] = args.region
    if args.status:
        order_context["order_status"] = args.status
    if args.fulfillment:
        order_context["fulfillment_type"] = args.fulfillment
    if args.final_sale:
        order_context["is_final_sale"] = True
    if args.prime:
        order_context["is_prime_member"] = True
    result = process_ticket(
        ticket_text=args.ticket,
        order_context=order_context if order_context else None
    )
    print("\n" + "=" * 60)
    print("RESOLUTION OUTPUT")
    print("=" * 60)
    print(f"\n[1] CLASSIFICATION : {result.classification.value.upper()} (confidence: {result.confidence})")
    print(f"\n[2] CLARIFYING QUESTIONS :", end="")
    if result.clarifying_questions:
        print()
        for q in result.clarifying_questions:
            print(f"      • {q}")
    else:
        print(" None")
    print(f"\n[3] DECISION       : {result.decision.value.upper()}")
    print(f"\n[4] RATIONALE      :")
    print(f"    {result.rationale}")
    print(f"\n[5] CITATIONS      :")
    if result.citations:
        for c in result.citations:
            print(f"    • {c.document} | {c.section} | chunk: {c.chunk_id}")
    else:
        print("    (none)")
    print(f"\n[6] CUSTOMER RESPONSE DRAFT :")
    print("-" * 40)
    print(result.customer_response)
    print("-" * 40)
    print(f"\n[7] NEXT STEPS / INTERNAL NOTES :")
    print(f"    {result.next_steps}")
    print(f"\n    Compliance : {'✓ PASSED' if result.compliance_passed else '✗ FAILED'}")
    if result.compliance_notes:
        print(f"    Notes      : {result.compliance_notes}")
    print("=" * 60)
def cmd_demo(args):
    from src.pipeline import SupportPipeline
    from src.models import SupportTicket, OrderContext
    pipeline = SupportPipeline()
    demo_tickets = [
        {
            "label": "APPROVE — Wrong item delivered",
            "ticket_text": "I ordered a bluetooth speaker but received a phone case instead. This is completely wrong. I want the correct item or a full refund.",
            "order_context": {
                "order_date": "2026-03-24",
                "order_id": "1234",
                "delivery_date": "2026-03-27",
                "item_category": "electronics",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "delivered",
                "order_value": 1499.0,
            }
        },
        {
            "label": "APPROVE — Late guaranteed delivery, wants shipping refund",
            "ticket_text": "I paid extra for One-Day Delivery but my order arrived 3 days late. I want my delivery charges refunded.",
            "order_context": {
                "order_date": "2026-03-23",
                "order_id": "1234",
                "delivery_date": "2026-03-27",
                "item_category": "apparel",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "delivered",
                "payment_method": "upi",
            }
        },
        {
            "label": "DENY — Opened innerwear, defective",
            "ticket_text": "I bought innerwear but after opening it I realized that it has a hole in it. I want to return it and get a refund.",
            "order_context": {
                "order_date": "2026-03-15",
                "order_id": "1234",
                "delivery_date": "2026-03-18",
                "item_category": "innerwear",
                "fulfillment_type": "first-party",
                "order_status": "delivered",
            }
        },
        {
            "label": "DENY — Already shipped, trying to cancel",
            "ticket_text": "I want to cancel my order right now. I just saw it has already been shipped but I don't want it anymore.",
            "order_context": {
                "order_date": "2026-03-26",
                "order_id": "1234",
                "item_category": "electronics",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "shipped",
            }
        },
        {
            "label": "ESCALATE — Marketplace seller not responding",
            "ticket_text": "I bought a saree from a third-party marketplace seller on Amazon. The product is completely different from what was shown in the listing. I messaged the seller 5 days ago and they have not replied at all The seller has exceeded the 3 business day response window. I want to file an A-to-Z Guarantee claim.",
            "order_context": {
                "order_date": "2026-03-10",
                "order_id": "1234",
                "delivery_date": "2026-03-14",
                "item_category": "apparel",
                "fulfillment_type": "marketplace-seller",
                "shipping_region": "India",
                "order_status": "delivered",
                "order_value": 2200.0,
            }
        },
        {
            "label": "ESCALATE — Missing package reported late (after 7 days)",
            "ticket_text": "My order was marked as delivered on 17th March 2026 but today is 29th March 2026 — that is 12 days ago — and I never received it. I know the policy says report within 7 days. I am reporting it late. I want a refund.",
            "order_context": {
                "order_date": "2026-03-10",
                "order_id": "1234",
                "delivery_date": "2026-03-17",
                "item_category": "electronics",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "delivered",
                "order_value": 5999.0,
            }
        },
        {
            "label": "EDGE — Non-returnable item but arrived damaged (exception)",
            "ticket_text": "I ordered a protein powder which I know is non-returnable. But when it arrived the seal was already broken and it smelled strange. Clearly tampered. I want a replacement.",
            "order_context": {
                "order_date": "2026-03-20",
                "order_id": "1234",
                "delivery_date": "2026-03-24",
                "item_category": "health supplement",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "delivered",
                "order_value": 1899.0,
            }
        },
        {
            "label": "EDGE — Not in policy (asks for custom compensation)",
            "ticket_text": "My delivery was 2 days late and I had to buy the same item from a local shop because I needed it urgently. I want Amazon to reimburse what I spent at the local shop. That is Rs 3500.",
            "order_context": {
                "order_date": "2026-03-20",
                "order_id": "1234",
                "delivery_date": "2026-03-25",
                "item_category": "electronics",
                "fulfillment_type": "first-party",
                "shipping_region": "India",
                "order_status": "delivered",
                "order_value": 3200.0,
            }
        },
    ]
    for i, t in enumerate(demo_tickets, 1):
        print(f"\n{'='*60}")
        print(f"DEMO TICKET {i} — {t['label']}")
        print(f"{'='*60}")
        print(f"Ticket: {t['ticket_text']}")
        ctx = OrderContext(**t["order_context"]) if t.get("order_context") else None
        ticket = SupportTicket(ticket_text=t["ticket_text"], order_context=ctx)
        result = pipeline.run(ticket)
        print(f"\n[1] Classification : {result.classification.value.upper()} ({result.confidence})")
        if result.clarifying_questions:
            print(f"[2] Clarifying Qs  : {result.clarifying_questions}")
        else:
            print(f"[2] Clarifying Qs  : None")
        print(f"[3] Decision       : {result.decision.value.upper()}")
        print(f"[4] Rationale      : {result.rationale[:150]}...")
        print(f"[5] Citations      : {len(result.citations)} — {[c.document for c in result.citations]}")
        print(f"[6] Customer Msg   : {result.customer_response}...")
        print(f"[7] Next Steps     : {result.next_steps[:500]}...")
        print()
    print("Demo complete.")
def main():
    parser = argparse.ArgumentParser(
        description="Amazon India Support Resolution Agent"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest_parser = subparsers.add_parser("ingest", help="Build the FAISS vector index")
    ingest_parser.set_defaults(func=cmd_ingest)
    run_parser = subparsers.add_parser("run", help="Process a single support ticket")
    run_parser.add_argument("--ticket", required=True, help="Customer ticket text")
    run_parser.add_argument("--category", help="Item category (apparel/electronics/perishable/hygiene/etc.)")
    run_parser.add_argument("--region", help="Shipping region (e.g. US-CA, UK, EU)")
    run_parser.add_argument("--status", help="Order status (placed/shipped/delivered/returned)")
    run_parser.add_argument("--fulfillment", help="Fulfillment type (first-party/marketplace-seller)")
    run_parser.add_argument("--final-sale", action="store_true", help="Mark item as final sale")
    run_parser.add_argument("--prime", action="store_true", help="Customer is a Prime member")
    run_parser.set_defaults(func=cmd_run)
    demo_parser = subparsers.add_parser("demo", help="Run example tickets")
    demo_parser.set_defaults(func=cmd_demo)
    args = parser.parse_args()
    args.func(args)
if __name__ == "__main__":
    main()
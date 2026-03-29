TEST_CASES = [
    {
        "id": "STD-001",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD123456789. I received a shirt 4 days ago. "
            "It is the wrong size and I never wore it. The tags are still on "
            "and it is in original packaging with the MRP tag intact. "
            "I want to return it and get a refund to my original payment method."
        ),
        "order_context": {
            "order_id": "OD123456789",
            "order_date": "2026-03-22",
            "delivery_date": "2026-03-25",
            "item_category": "apparel",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 899.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Unused apparel within return window, original condition. Clear approve.",
    },
    {
        "id": "STD-002",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD987654321. I placed an order 15 minutes ago for a mixer grinder. "
            "I made a mistake and want to cancel it immediately. "
            "The order status still shows as placed and has not been shipped yet."
        ),
        "order_context": {
            "order_id": "OD987654321",
            "order_date": "2026-03-29",
            "item_category": "kitchen appliance",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "placed",
            "payment_method": "upi",
            "order_value": 2499.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Order placed, not yet shipped. Cancel before shipping = approve.",
    },
    {
        "id": "STD-003",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD111222333. My order was delivered 2 days ago but I never received it. "
            "I checked with my neighbours and building security — nothing is there. "
            "The tracking says delivered but I did not get it. "
            "I am reporting this within the required 7 days. I want a refund."
        ),
        "order_context": {
            "order_id": "OD111222333",
            "order_date": "2026-03-20",
            "delivery_date": "2026-03-27",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 3499.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Package shows delivered but not received. Reported within 7 days. Approve investigation.",
    },
    {
        "id": "STD-004",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD444555666. I want to cancel this order. "
            "I just checked and the order has already been shipped and is out for delivery. "
            "The tracking shows it is with the courier. I do not want this item anymore."
        ),
        "order_context": {
            "order_id": "OD444555666",
            "order_date": "2026-03-27",
            "item_category": "apparel",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "shipped",
            "payment_method": "debit_card",
            "order_value": 1299.0,
        },
        "expected_decision": "deny",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Order already shipped. Cancellation not possible. Must return after delivery. Deny.",
    },
    {
        "id": "STD-005",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD777888999. I paid for One-Day Delivery and the promised date "
            "was 25th March 2026. My order actually arrived on 28th March 2026 — "
            "that is 3 days late. I want my delivery charges refunded."
        ),
        "order_context": {
            "order_id": "OD777888999",
            "order_date": "2026-03-24",
            "delivery_date": "2026-03-28",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "upi",
            "order_value": 5999.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Late guaranteed One-Day delivery. Amazon automatically refunds delivery charges to Amazon Pay balance. Approve.",
    },
    {
        "id": "STD-006",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD100200300. I received a bluetooth headset in my order "
            "but I ordered a bluetooth speaker. These are completely different products. "
            "I want the correct item delivered or a full refund. "
            "I am a first-party Amazon order, delivered yesterday."
        ),
        "order_context": {
            "order_id": "OD100200300",
            "order_date": "2026-03-25",
            "delivery_date": "2026-03-28",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 1499.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Wrong item delivered. First-party. Policy clearly covers this. Approve refund or replacement.",
    },
    {
        "id": "STD-007",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD400500600. I ordered pet food — a 5kg bag of dog food. "
            "I received it 3 days ago, opened the bag, and my dog refuses to eat it. "
            "I want to return the opened bag and get a refund. "
            "There is nothing wrong with the product — my dog just does not like it."
        ),
        "order_context": {
            "order_id": "OD400500600",
            "order_date": "2026-03-22",
            "delivery_date": "2026-03-25",
            "item_category": "pet food",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "upi",
            "order_value": 1199.0,
        },
        "expected_decision": "deny",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Pet food is explicitly non-returnable consumable. Opened + buyer's remorse. Deny.",
    },
    {
        "id": "STD-008",
        "category": "standard",
        "ticket_text": (
            "Order ID: OD700800900. Amazon cancelled my order without any request from me. "
            "I never asked for the cancellation. My payment was already deducted from my account. "
            "I want to know where my refund is and when I will receive it."
        ),
        "order_context": {
            "order_id": "OD700800900",
            "order_date": "2026-03-26",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "cancelled",
            "payment_method": "net_banking",
            "order_value": 8999.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Amazon-initiated cancellation. Full refund to original payment method. Approve.",
    },
    {
        "id": "EXC-001",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD001002003. I bought innerwear 5 days ago and opened the package. "
            "The size is completely wrong — I ordered Large but received Small. "
            "I want to return the opened innerwear and get a refund. "
            "The product has no defects, I just got the wrong size."
        ),
        "order_context": {
            "order_id": "OD001002003",
            "order_date": "2026-03-22",
            "delivery_date": "2026-03-24",
            "item_category": "innerwear",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "upi",
            "order_value": 399.0,
        },
        "expected_decision": "deny",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Opened innerwear, wrong size, no defect. Non-returnable hygiene item. Deny.",
    },
    {
        "id": "EXC-002",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD004005006. I ordered a face cream that is marked as non-returnable. "
            "When it arrived today the seal was already broken and the product looks used — "
            "there are fingerprints inside the jar. This is clearly tampered or used stock. "
            "I want a refund even though it is listed as non-returnable."
        ),
        "order_context": {
            "order_id": "OD004005006",
            "order_date": "2026-03-26",
            "delivery_date": "2026-03-29",
            "item_category": "personal care",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 1299.0,
            "is_final_sale": False,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Non-returnable BUT arrived tampered/damaged. Exception applies. Approve.",
    },
    {
        "id": "EXC-003",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD007008009. My order of mithai arrived today and the box is completely "
            "crushed — the sweets are broken and the packaging is damaged. I am reporting this "
            "on the same day as delivery. I cannot return food obviously but I want a refund. "
            "The item was fulfilled directly by Amazon."
        ),
        "order_context": {
            "order_id": "OD007008009",
            "order_date": "2026-03-28",
            "delivery_date": "2026-03-29",
            "item_category": "food",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "upi",
            "order_value": 650.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Damaged food reported same day. Non-returnable but damaged = refund eligible. Approve.",
    },
    {
        "id": "EXC-004",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD010011012. I just received a new smartphone today. "
            "I unboxed it and pressed the power button but it does not turn on at all. "
            "The phone is completely dead — it will not respond to charging either. "
            "This is a Dead on Arrival unit. I want a replacement or full refund."
        ),
        "order_context": {
            "order_id": "OD010011012",
            "order_date": "2026-03-26",
            "delivery_date": "2026-03-29",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 15999.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Dead on arrival electronics. Free replacement or full refund. Approve.",
    },
    {
        "id": "EXC-005",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD013014015. I received a bag of pet food today. "
            "I checked the expiry date on the bag and it expires in just 2 days — "
            "on 31st March 2026. Today is 29th March 2026. "
            "I cannot use a 5kg bag in 2 days. I want a refund or replacement."
        ),
        "order_context": {
            "order_id": "OD013014015",
            "order_date": "2026-03-27",
            "delivery_date": "2026-03-29",
            "item_category": "pet food",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "debit_card",
            "order_value": 1199.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Near-expired product. Even non-returnable consumables qualify for refund if expired/near-expired. Approve.",
    },
    {
        "id": "EXC-006",
        "category": "exception",
        "ticket_text": (
            "Order ID: OD016017018. I bought a trimmer 2 days ago, opened it and used it once. "
            "It makes a very loud grinding noise and vibrates abnormally. "
            "This is clearly a manufacturing defect — a normal trimmer does not sound like this. "
            "I want to return the defective trimmer and get a replacement."
        ),
        "order_context": {
            "order_id": "OD016017018",
            "order_date": "2026-03-25",
            "delivery_date": "2026-03-27",
            "item_category": "personal care",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "upi",
            "order_value": 1799.0,
        },
        "expected_decision": "approve",
        "should_escalate": False,
        "should_abstain": False,
        "notes": "Defective personal care device after first use. Defect exception applies even if opened. Approve.",
    },
    {
        "id": "CON-001",
        "category": "conflict",
        "ticket_text": (
            "Order ID: OD019020021. I bought a saree from a third-party marketplace seller "
            "on Amazon 19 days ago. The product received is completely different from what "
            "was shown in the listing — wrong colour, wrong fabric. "
            "I contacted the seller through Amazon messaging 6 days ago and they have "
            "not replied at all. The seller has exceeded the 3 business day response window. "
            "I want to file an A-to-Z Guarantee claim for a full refund."
        ),
        "order_context": {
            "order_id": "OD019020021",
            "order_date": "2026-03-10",
            "delivery_date": "2026-03-13",
            "item_category": "apparel",
            "fulfillment_type": "marketplace-seller",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 2200.0,
        },
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": False,
        "notes": "Marketplace seller unresponsive 6 days. A-to-Z Guarantee. Must escalate — agent cannot approve A-to-Z directly.",
    },
    {
        "id": "CON-002",
        "category": "conflict",
        "ticket_text": (
            "Order ID: OD022023024. I bought a jacket from a marketplace seller on Amazon. "
            "The product listing clearly stated a 30-day return window. "
            "It has been 15 days since delivery and I want to return the item. "
            "The seller is now saying I only have 7 days to return and is refusing my return request. "
            "The seller's policy contradicts what was shown on the listing page."
        ),
        "order_context": {
            "order_id": "OD022023024",
            "order_date": "2026-03-11",
            "delivery_date": "2026-03-14",
            "item_category": "apparel",
            "fulfillment_type": "marketplace-seller",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "debit_card",
            "order_value": 1899.0,
        },
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": False,
        "notes": "Seller policy conflicts with listing. Escalate to A-to-Z / marketplace dispute team.",
    },
    {
        "id": "CON-003",
        "category": "conflict",
        "ticket_text": (
            "Order ID: OD025026027. I bought electronics from a marketplace seller on Amazon. "
            "The item I received is clearly a counterfeit — the brand logo looks fake, "
            "the build quality is terrible, and it does not match the product listing at all. "
            "I messaged the seller 4 days ago through Amazon and got no response. "
            "I want Amazon to intervene and give me a full refund."
        ),
        "order_context": {
            "order_id": "OD025026027",
            "order_date": "2026-03-01",
            "delivery_date": "2026-03-05",
            "item_category": "electronics",
            "fulfillment_type": "marketplace-seller",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 4999.0,
        },
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": False,
        "notes": "Counterfeit item, unresponsive seller. A-to-Z Guarantee. Escalate.",
    },
    {
        "id": "NIP-001",
        "category": "not-in-policy",
        "ticket_text": (
            "I want to know the exact address and phone number of the Amazon warehouse "
            "that is currently handling my order OD028029030. "
            "I want to call them directly and speak to the warehouse manager about my order."
        ),
        "order_context": {
            "order_id": "OD028029030",
            "order_date": "2026-03-27",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "placed",
            "payment_method": "upi",
        },
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": True,
        "notes": "Warehouse contact details not in any policy. Must abstain and redirect to customer service.",
    },
    {
        "id": "NIP-002",
        "category": "not-in-policy",
        "ticket_text": (
            "I want to understand the exact internal steps Amazon takes when investigating "
            "a stolen package claim. What databases do you check? What evidence thresholds "
            "are required internally before you approve or deny a claim? "
            "I need this information for a consumer rights complaint I am filing."
        ),
        "order_context": None,
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": True,
        "notes": "Internal investigation procedures not in policy docs. Must abstain.",
    },
    {
        "id": "NIP-003",
        "category": "not-in-policy",
        "ticket_text": (
            "Order ID: OD031032033. My One-Day Delivery order was 2 days late. "
            "Because of this I had to urgently buy the same item from a local shop "
            "and spent Rs 3500 extra. I want Amazon to reimburse me Rs 3500 "
            "for what I spent at the local shop due to the late delivery. "
            "This is a reasonable request and I expect full compensation."
        ),
        "order_context": {
            "order_id": "OD031032033",
            "order_date": "2026-03-24",
            "delivery_date": "2026-03-27",
            "item_category": "electronics",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "credit_card",
            "order_value": 3200.0,
        },
        "expected_decision": "needs_escalation",
        "should_escalate": True,
        "should_abstain": True,
        "notes": "Reimbursement for third-party purchases not in any policy. Must abstain and not invent compensation rules. Only shipping fee refund is covered by policy.",
    },
]
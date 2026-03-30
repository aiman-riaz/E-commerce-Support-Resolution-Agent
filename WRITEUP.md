WRITE-UP: E-COMMERCE SUPPORT RESOLUTION AGENT
Purple Merit Technologies — AI/ML Engineer Intern Assessment 2
Submitted by: Aiman Ahmed Riaz | March 2026

ARCHITECTURE OVERVIEW

The system is a 4-agent sequential pipeline backed by a RAG retrieval layer:

  Customer Ticket + Order Context (JSON)
            |
            v
  [ 1. Triage Agent ]          Classifies issue type, flags missing fields
            |
            v
  [ 2. Policy Retriever ]      FAISS semantic search, top-7 chunks with citations
            |
            v
  [ 3. Resolution Writer ]     Drafts decision using ONLY retrieved chunks
            |
            v
  [ 4. Compliance/Safety ]     Checks for unsupported claims, missing citations
            |
            v
  Structured ResolutionOutput (7 required fields)

All agents use Groq (openai/gpt-oss-20b) at temperature=0.
All outputs are JSON-validated via Pydantic models.

AGENT RESPONSIBILITIES AND PROMPTS (HIGH LEVEL)

Agent 1 — Triage Agent
  Classifies issue type (refund / shipping / cancellation / dispute / promo / payment / fraud / other),
  identifies missing fields, generates up to 3 clarifying questions if critical info is missing.
  Key prompt constraint: "Do NOT make any policy decisions — just classify and flag missing info."

Agent 2 — Policy Retriever Agent
  Builds a focused semantic search query from ticket text and triage output.
  Retrieves top-7 most relevant policy chunks from FAISS with doc/section/chunk_id citations.
  No LLM call — pure vector similarity search using all-MiniLM-L6-v2 embeddings.

Agent 3 — Resolution Writer Agent
  Drafts decision, rationale, customer response, and next steps using ONLY retrieved chunks.
  Key constraints: marketplace seller disputes always escalate; non-returnable items that arrive
  damaged or defective are approved (exception applies); DOA electronics approved directly.
  Outputs one of: approve / deny / partial / needs_escalation / need_more_info.

Agent 4 — Compliance/Safety Agent
  Checks if citations exist in the draft. Auto-approves if citations are present.
  Flags for review if no citations found. Simplified to citation-presence check to
  avoid false positives from smaller models generating overly strict compliance failures.

DATA SOURCES

12 documents sourced from Amazon India public help pages (amazon.in), accessed March 29, 2026.
All pages are publicly accessible. Full URLs in data/policies/sources.md.

Coverage:
  Returns and refunds (including exceptions) — POL-01, POL-02, POL-09
  Cancellations — POL-03
  Shipping and delivery / lost package — POL-04, POL-10
  Promotions and coupon terms — POL-07
  Disputes (damaged/incorrect/missing items) — POL-05, POL-06

Chunking strategy: RecursiveCharacterTextSplitter, chunk_size=500 chars, overlap=50 chars.
Rationale: Policy sections fit in ~500 chars. 50-char overlap prevents boundary cut-offs.
Embeddings: sentence-transformers/all-MiniLM-L6-v2 — free, CPU-only, no API key needed.
Vector store: FAISS (CPU), cosine similarity, top-7 retrieval per query.

EVALUATION SUMMARY

Test set: 20 tickets — 8 standard, 6 exception-heavy, 3 conflict, 3 not-in-policy.
Model: Groq openai/gpt-oss-20b

Best run results:

  Citation coverage rate   : 100%    (20/20 had at least 1 citation)
  Decision correctness     : 65-75%  (13-15/20 correct)
  Escalation accuracy      : 70%     (14/20 correct escalation behavior)
  Abstention accuracy      : 66-100% (2-3/3 not-in-policy cases abstained correctly)
  Compliance pass rate     : 100%    (20/20 passed compliance check)
  Unsupported claim rate   : 0%      (0/20 hallucinated policy claims)

By category:
  Standard cases    : 87.5%  — strong after adding full order context to all test cases
  Exception cases   : 50-66% — harder due to multi-rule reasoning (non-returnable + exception)
  Conflict cases    : 33-100% — most variable category, depends on A-to-Z escalation routing
  Not-in-policy     : 66-100% — agent correctly abstains in most cases

KEY FAILURE MODES

1. Marketplace disputes sometimes approved instead of escalated.
   Model finds the underlying policy (wrong item received) and approves directly,
   ignoring that seller-involved cases must go through A-to-Z.
   Fix: Explicit rule in prompt — any marketplace seller dispute must be escalated.

2. Smaller models (8B) default to needs_escalation as a safe fallback.
   Model treats uncertainty as escalation trigger rather than making a decision.
   Fix: Switched to 70B model with explicit decision guide naming every case.

3. Groq daily token limit (500k/day) causes mid-eval failures.
   Cases after the limit show NO CITE and default to needs_escalation.
   Fix: 5-second sleep between cases, auto-retry on rate limit, switched to 70B quota.

4. Test cases missing order context triggered need_more_info from Triage agent.
   The 70B model responsibly asks for Order ID before deciding.
   Fix: All 20 test cases include full order context.

WHAT I WOULD IMPROVE NEXT

1. Cross-encoder re-ranking after initial FAISS retrieval to improve chunk selection,
   especially for exception cases where both the rule and the exception clause need to be found.

2. Metadata-filtered retrieval — tag each chunk by policy type and filter by triage output
   before semantic search to reduce noise.

3. LangGraph retry loop — let Compliance Agent trigger rewrite requests (up to 2 retries)
   instead of immediately escalating on citation failures.

4. Human-annotated evaluation set reviewed by a support domain expert
   for more reliable accuracy metrics.

5. Streaming output in Streamlit demo — current pipeline latency is 8-15 seconds
   with the 70B model; streaming would significantly improve perceived responsiveness.

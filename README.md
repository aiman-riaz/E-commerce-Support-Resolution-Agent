# E-commerce Support Resolution Agent

A multi-agent RAG system that resolves e-commerce customer support tickets using Amazon India policy documents. Built with LangChain, FAISS, and Groq.

---

## How It Works

Give it a support ticket and order details. It runs through 4 agents and gives a structured resolution:

```
Triage → Policy Retriever → Resolution Writer → Compliance Check
```

Every decision is backed by citations from the policy documents. If the policy doesn't cover the situation, it escalates instead of guessing.

---

## Project Structure

```
ecommerce-support-agent/
├── data/policies/          ← 12 Amazon India policy documents
├── src/
│   ├── models.py           ← Input/output schemas (Pydantic)
│   ├── ingestion.py        ← Doc loading, chunking, FAISS indexing
│   ├── agents.py           ← All 4 agent classes
│   └── pipeline.py         ← Runs agents in sequence
├── evaluation/
│   ├── test_cases.py       ← 20 test tickets
│   └── run_eval.py         ← Evaluation runner
├── main.py                 ← CLI entry point
├── app.py                  ← Streamlit demo UI
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and create virtual environment

```cmd
git clone https://github.com/aiman-riaz/ecommerce-support-resolution-agent.git
cd ecommerce-support-resolution-agent
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```cmd
pip install -r requirements.txt
```

### 3. Set up API key

```cmd
copy .env.example .env
```

Open `.env` and fill in your Groq API key (free at console.groq.com):

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your-key-here
GROQ_MODEL=openai/gpt-oss-20b
```

### 4. Build the vector index (run once)

```cmd
python main.py ingest
```

---

## Running

### Demo (8 example tickets)

```cmd
python main.py demo
```

### Single ticket from CLI

```cmd
python main.py run --ticket "I received a wrong item, I want a refund" --category electronics --status delivered
```

### Streamlit UI

```cmd
streamlit run app.py
```

### Evaluation (all 20 test cases)

```cmd
python -m evaluation.run_eval
```

Results saved to `evaluation/report.txt` and `evaluation/results.json`.

---

## Output Format

Every ticket produces 7 fields:

```
[1] Classification    issue type + confidence
[2] Clarifying Qs     asked only if critical info is missing
[3] Decision          approve / deny / partial / needs_escalation / need_more_info
[4] Rationale         policy-based reasoning with citation references
[5] Citations         document + section + chunk ID for every claim
[6] Customer Response customer-ready message
[7] Next Steps        internal notes for the support agent
```

---

## Evaluation Results

| Metric | Score |
|--------|-------|
| Citation coverage | 100% |
| Decision correctness | 65–75% |
| Compliance pass rate | 100% |
| Unsupported claim rate | 0% |
| Abstention accuracy (not-in-policy) | 66–100% |

---

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Framework | LangChain 0.2 | Stable, well-documented |
| LLM | Groq openai/gpt-oss-20b | Free, fast, follows instructions reliably |
| Embeddings | all-MiniLM-L6-v2 | Free, CPU-only, no API key |
| Vector store | FAISS | Lightweight, offline, fast |
| Validation | Pydantic | Structured JSON outputs |
| UI | Streamlit | Quick demo setup |

# 🌿 Greenwash Swarm — Automated ESG Integrity Platform

> A 5-agent LangGraph swarm that detects greenwashing by comparing what companies *tell regulators* (ESG PDFs) vs. what they *tell the public* (social media).

## Architecture

```
┌─────────────────── SUPERVISOR (LangGraph StateGraph) ─────────────────────┐
│                                                                             │
│   [A1] Harvester ──────────────────────── [A2] Social Monitor              │
│   PDF → Claims + OCR fallback             Crawl4AI virtual scroll          │
│   (runs in parallel with A2)              Stealth mode + screenshots        │
│                        │                            │                       │
│                        └──────────── ▼ ─────────────┘                      │
│                              [B] Auditor                                    │
│                        ClimateBERT + FinBERT-ESG                           │
│                        Hyperbole heuristic + Discrepancy compare           │
│                                    │                                        │
│                              [C] Fact-Checker                               │
│                       ChromaDB RAG + Tavily web search                     │
│                                    │                                        │
│                              [D] Judge                                      │
│                      Greenwash Index (0–100) + Reasoning Trail             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                          Next.js Dashboard (port 3000)
```

## Agent Roles

| Agent | Tool | Role |
|---|---|---|
| A1 Harvester | unstructured + pytesseract | PDF → structured claims, OCR for image-heavy reports |
| A2 Social Monitor | Crawl4AI + Playwright | Scroll social feeds, screenshot flagged posts |
| B Auditor | ClimateBERT + FinBERT-ESG | Classify & score every claim for hyperbole |
| C Fact-Checker | ChromaDB + Tavily | Cross-check claims against benchmarks + live web |
| D Judge | LangChain reasoning | Final Greenwash Index + documented reasoning trail |

## Quick Start (Docker)

```bash
cp .env.example .env
# Fill in TAVILY_API_KEY (optional but recommended)
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs

## Manual Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # for Crawl4AI stealth browser
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install && npm run dev
```

## Usage

1. Open `http://localhost:3000`
2. Upload an ESG PDF report
3. (Optional) Paste a company LinkedIn / newsroom URL for social monitoring
4. Click **Analyze** — watch the Swarm agents work in real-time
5. Review the Dashboard:
   - **Risk Gauge** (0–100)
   - **Claims Table** (color-coded: 🔴 Vague / 🟡 Partial / 🟢 Verified)
   - **Discrepancy View** — PDF claim vs. social media post + screenshot proof
   - **Reasoning Trail** — which agent flagged what and why

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TAVILY_API_KEY` | Optional | Enables live web search in Fact-Checker |
| `PINECONE_API_KEY` | Optional | Use Pinecone instead of local ChromaDB |
| `HF_TOKEN` | Optional | Required for gated Hugging Face models |
| `SCROLL_SCREENSHOT_DIR` | Auto | Defaults to `data/screenshots` |

## Greenwash Risk Scoring

```
Greenwash Index = (Auditor Flags × 0.4) + (Fact Divergence × 0.4) + (Vagueness × 0.2)

HIGH sentiment (>0.80) + ZERO numbers → 🔴 HIGH RISK
HIGH sentiment (>0.55) + ZERO numbers → 🟡 MEDIUM RISK  
PDF claim contradicted by Social post  → 🔴 DISCREPANCY FLAG
Claim confirmed by ChromaDB benchmark  → 🟢 VERIFIED
```
# greenwashing-swarm

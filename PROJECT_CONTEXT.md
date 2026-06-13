# CertOps AI — Project Context File
> **This file is the single source of truth for all AI agents and developers working on this project.**
> Read this entire file before writing any code, suggesting any changes, or making any architectural decisions.
> Update this file after every development session.

---

## Last Updated
- Date: 2026-06-13
- Session: **UI FLOW REWORK** — Simplified the frontend to a single `st.session_state.view` state machine, eliminated backend-driven routing, reduced `st.rerun()` usage, and made exam navigation explicit with radio-based answer selection.
- Status: Frontend now follows four explicit views: landing, analyzing, exam, results. Exam flow is stable and user-controlled, with no unexpected resets.
- Updated by: Arun

---

## Changelog
- 2026-06-13 (Latest): **UI FLOW REWORK** — Reworked frontend routing to a single state machine using `st.session_state.view`. The app now uses four explicit views: landing, analyzing, exam, results. Removed backend-driven routing and overlapping state checks, replaced auto-advance exam behavior with explicit radio selection and Previous/Next/Finish navigation, and eliminated unexpected reset behavior. Added results-page council pass/fail analysis with agent-level outcome matching so learners can compare readiness council predictions against actual mock exam performance.
- 2026-06-12 (Earlier): **INTERACTIVE QUIZ + RESOURCE FIXES** — Fixed 3 critical functional gaps: (1) Pipeline now pauses after Phase 2 (council) with interactive_assessment=True — user takes a real interactive exam with one question at a time, timer, immediate feedback. (2) Answers submitted via new POST /pipeline/continue endpoint which evaluates real answers (not simulated) and runs coaching + reflection phases using run_coaching_phase() and continue_pipeline_after_assessment(). (3) Added _fetch_learning_resources() to orchestrator that fetches resources for ALL skill map topics (deduped with weak_topics, max 8) using deterministic ResourceFinder. New render_resource_section() shows all 4 categories (Official, MVP, Videos, Practice) with clickable target='_blank' links and FREE/PAID badges. Learning resources displayed in tabbed interface on result page. Added run_coaching_phase() method to orchestrator. Debug logging throughout ([DEBUG] prints). learning_resources and pipeline_state now returned in GET /state. Removed old auto-simulate assessment path from pipeline. Added ContinueRequest model and POST /pipeline/continue endpoint to main.py.
- 2026-06-12 (Earlier): **PREMIUM SAAS UI REDESIGN** — Complete frontend app.py overhaul implementing 10 premium design tasks: (1) Hero landing section with gradient title, radial gradient background, "Powered by Azure AI Foundry" badge. (2) Glass morphism input card with backdrop-filter blur, hover border glow. (3) Animated agent activity feed with typing dots, pulse animation. (4) Council debate as alternating left/right chat bubbles with staggered appearance. (5) Verdict reveal with animated SVG confidence ring, gradient-ambient background. (6) Modern render_stat_card() with icon, decorative blob, trend indicator. (7) Skill tags as pill-shaped chips with hover lift, weak topics in red. (8) Premium exam question cards with gradient border, topic badge, letter answer badges. (9) Skeleton loading shimmer utility. (10) Sidebar circular SVG progress ring. Global CSS design system with color tokens (DS dict). Button hover lift on all elements. Streamlit overrides for inputs, sliders, tabs, progress bars, metrics, expanders.
- 2026-06-12 (Earlier): **DETERMINISTIC RESOURCE FINDER** — Rewrote backend/plugins/resource_finder.py as fully deterministic, zero-hallucination resource bundle generator. ResourceFinder now synchronous. No LLM calls. No AzureOpenAI imports remain. All URLs use only trusted domains: learn.microsoft.com, youtube.com, github.com, techcommunity.microsoft.com. MVP sources include John Savill YouTube search and Tech Community discussions. Added caching for instant repeat lookups. MS Learn Catalog API with guaranteed fallback to search URL. Updated frontend MVP rendering with gold/amber (#ffa502) styled resource cards matching new data format.
- 2026-06-12 (Earlier): **AUTOMATED PIPELINE ORCHESTRATION** — Implemented run_full_pipeline() in Orchestrator with 6-phase sequential execution (Learning → Council → Assessment → Coaching → Reflection). Added _check_council_discrepancies() and _adapt_learning_plan() for automatic study plan adaptation when council finds issues or assessment fails. Added POST /pipeline endpoint for single-button orchestration and GET /pipeline/status for progress tracking. Completely rewrote frontend: primary view is single automated pipeline with form input + "Run Full Analysis" button triggering all phases in sequence with live progress bar and phase-by-phase result display. Consolidated report shows verdict, score, adaptations made, and final study plan. Multi-page deep-dive navigation remains in sidebar (Council Debate, Manager Insights, Agent Reputation, Reasoning Trace) for read-only inspection. No manual page navigation needed for core flow.
 - 2026-06-12 (UX REDESIGN): **FLUID SINGLE-FLOW UX** — Introduced a linear journey with progressive disclosure. Replaced multi-page sidebar navigation for core flow with a sticky progress strip, stepped wizard, and collapsed completed step summaries. Frontend now treats the journey as one linear flow: Landing → Run Analysis → Council → Exam → Results (with tabs). Added contextual running animations, deterministic resource topics, and a reset that clears both frontend and backend demo state. Routing is now driven by frontend session state rather than pipeline state returned from the API.
- 2026-06-12 (Earlier): **VALIDATION & CONNECTIVITY** — Fixed orchestrator singleton pattern with startup logging. Added GET /state endpoint for memory inspection. Created frontend/state.py as centralized API client with error handling and phase guard functions. Completely rewrote all 7 Streamlit pages with improved UX: phase guards prevent skipping steps, st.status() provides step-by-step feedback for long LLM calls, sidebar shows session status and system health, status badges show completion. Response times now visible with "Building learning plan..." multi-step status boxes. All endpoints handle timeouts gracefully (120s for LLM calls). Added /health system status expander in sidebar. End-to-end flow validated: learner dashboard → council → assessment → coaching → manager insights → reputation → trace.
- 2026-06-10 (Earlier): **FEATURE COMPLETE** — Built self-learning layer with Reflection Agent and Manager Insights. ReflectionAgent compares council predictions vs actual exam outcomes, updates agent reputations in SQLite, and generates analytical insights via LLM. ManagerInsightsAgent provides team-level analytics including certification readiness, at-risk learners, and topic weakness patterns. All 7 Streamlit pages now complete: Manager Insights (team dashboard), Agent Reputation (leaderboard with animated bars), and Reasoning Trace (execution log). Added POST /reflection, GET /manager, and GET /reset-demo endpoints. System now self-improves: each assessment updates agent weights for future council verdicts.
- 2026-06-10 (Earlier): Built Assessment Agent and Socratic Coach. AssessmentAgent generates 10 mock exam questions via LLM, evaluates answers with topic-level scoring, saves results to SQLite, and triggers Socratic coaching on failure. SocraticCoach diagnoses root misconceptions using LLM and generates 3 guided questions using the Socratic method. Streamlit Pages 3 and 4 fully implemented with quiz UI, results review, and progressive Socratic question flow. Added POST /submit endpoint for answer submission.
- 2026-06-10 (Earlier): Built the Readiness Council — the centerpiece of CertOps AI. Implemented all 5 specialist agents (Optimist, Skeptic, Advocate, Historian, RiskAnalyst) with parallel execution. Critic Agent synthesizes weighted votes with safety rules. Reputation Engine complete with SQLite backing. Streamlit Page 2 now shows 5 agent cards side-by-side with colored verdicts + prominent Critic verdict box. FastAPI /readiness endpoint fully wired and tested.
- 2026-06-09 (Earlier): Integrated Azure AI Foundry IQ as primary knowledge source with cascading fallback (Foundry → Dynamic Web/LLM → Offline). Created knowledge_router.py for clean abstraction. Updated LearningAgent with citation tracking. Added Streamlit badges showing knowledge source. Created helper script find_connection_string.py. Added USE_FOUNDRY_IQ feature flag.
- 2026-06-09 (Earlier): Replaced KnowledgePlugin with DynamicKnowledgePlugin (web scraping + LLM fallback); made certification input free-text; fixed Study Windows duration display ("Noneh" → "1.5h"); StudyPlanAgent and EngagementAgent now fully dynamic; added beautifulsoup4, requests, lxml to requirements.
- 2026-06-09 (Initial): Implemented SK kernel, KnowledgePlugin, HistoryPlugin, LearningAgent, StudyPlanAgent, EngagementAgent; wired into Orchestrator and FastAPI `/learn`; updated Streamlit Learner Dashboard.


---

## Project Identity

| Field | Value |
|---|---|
| **Name** | CertOps AI |
| **Full Title** | Self-Learning Certification Readiness Intelligence Platform |
| **Hackathon** | Microsoft Agents League Hackathon 2026 |
| **Track** | Reasoning Agents (Microsoft Foundry) |
| **Deadline** | June 14, 2026 |
| **GitHub** | https://github.com/arungajapathi-hash/CertOps-AI |
| **Developer** | Arun (solo) |

---

## One-Sentence Architecture
> CertOps AI uses a council of specialized reasoning agents to assess certification readiness, challenges their conclusions through structured debate, diagnoses failures through Socratic coaching, and continuously improves future recommendations using a reputation-based learning system.

**Do not change this sentence. Use it verbatim in README, demo, and pitch.**

---

## Ideology — Non-Negotiable Principles

1. **Agents debate, not report** — the council argues with each other. Output is a verdict from conflict, not a summary from consensus.
2. **Grounded, not hallucinated** — every recommendation cites a source from Foundry IQ knowledge base.
3. **System learns from failure** — every wrong prediction updates agent reputation. Future verdicts improve automatically.
4. **Diagnose, don't just score** — when a learner fails, the system explains exactly why, not just what score they got.
5. **Shared memory, no direct agent talk** — agents communicate only through shared memory dict. No agent calls another agent directly.

---

## Problem Statement
Enterprise engineering teams manage certification programmes blindly. When engineers fail exams, nobody knows why. Study plans are generic. Managers have no real-time visibility. The same failures repeat every quarter.

## Solution
A multi-agent system that builds personalised study plans, convenes an adversarial readiness council before the exam, diagnoses failure root causes after, and improves its own accuracy over time using agent reputation scores.

---

## UI Design System — Color Tokens

```python
DS = {
    "primary":    "#4f8ef7",   # Azure blue
    "secondary":  "#a855f7",   # Purple accent
    "success":    "#00c896",   # Green
    "danger":     "#ff4757",   # Red
    "warning":    "#ffa502",   # Amber/gold
    "bg_card":    "rgba(255,255,255,0.04)",
    "border":     "rgba(255,255,255,0.1)",
    "border_hover": "rgba(79,142,247,0.4)",
    "text_primary":   "#f0f0f0",
    "text_secondary": "#8b8b9e",
    "shadow":     "0 8px 32px rgba(0,0,0,0.3)",
    "gradient_btn":   "linear-gradient(135deg, #4f8ef7, #a855f7)",
    "gradient_bg":    "radial-gradient(circle at 50% 0%, rgba(79,142,247,0.15) 0%, transparent 60%)",
}
```

**Component Styles:**
- **Cards**: Glass morphism (`backdrop-filter: blur(20px)`), border `rgba(255,255,255,0.1)`, hover accent glow
- **Primary buttons**: Gradient background `#4f8ef7 → #a855f7`, border-radius 12px, hover lift -2px Y, box-shadow 0 4px 20px
- **Secondary buttons**: Transparent with white border, hover brighten
- **Progress bars**: Gradient fill, 8px height, rounded corners
- **Skill tags**: Pill shape 20px radius, hover lift + box-shadow, weak variant in red
- **Exam letters**: 36px square badges, filled blue when selected, rounded 10px
- **Verdict ring**: SVG `stroke-dasharray` with 1.5s transition, 140px diameter
- **Stat cards**: Decorative blob top-right, uppercase labels, trend arrows with up/down
- **Chat bubbles**: Alternating left/right alignment, colored translucent backgrounds, italic quotes
- **Inputs**: Dark glass background, focus glow with 3px ring
- **Skeleton shimmer**: Animated gradient sweep 1.5s infinite

## Tech Stack — FROZEN

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Streamlit | Community Cloud for hosting |
| API | FastAPI | Thin layer only — 8 endpoints |
| Agent Framework | Semantic Kernel (Python) 1.3.0 | SK Plugins for knowledge, history, assessment, reputation |
| LLM | Azure OpenAI GPT-4o | Single deployment, all agents |
| AI Platform | Azure AI Foundry | Primary knowledge source + orchestration |
| Knowledge (Primary) | Foundry IQ (RAG) | Indexed certification documents, grounded retrieval |
| Knowledge (Fallback) | DynamicKnowledgePlugin | Web scraping + LLM generation (cascading) |
| Web Scraping | requests + BeautifulSoup4 + lxml | For Microsoft Learn exam objectives (fallback) |
| Memory | SharedMemory class (Python dict) | In-memory per session |
| Database | SQLite | 4 tables only — no exceptions |
| Charts | Plotly | Agent reputation + readiness trend |
| Config | python-dotenv | .env file |

**Do not add new dependencies without updating this file and confirming with Arun.**

---

## Knowledge Retrieval Cascade — Design Pattern

All certification knowledge flows through a **cascading fallback chain** designed for reliability + transparency:

```
┌─────────────────────────────────────────────────────────────────┐
│ LearningAgent.execute() calls get_knowledge_plugin()            │
├─────────────────────────────────────────────────────────────────┤
│ 1. FoundryKnowledgePlugin (Primary)                             │
│    ├─ Attempts AIProjectClient.create_and_run_thread()          │
│    ├─ Falls back to knowledge_bases.search()                    │
│    └─ Returns: {"content": str, "citations": [], "source": ...} │
│                                                                  │
│ 2. DynamicKnowledgePlugin (Fallback-1) [if Foundry fails]       │
│    ├─ Scrapes https://learn.microsoft.com (5s timeout)          │
│    ├─ Falls back to LLM generation if scrape fails              │
│    └─ Caches results per certification                          │
│                                                                  │
│ 3. Offline Hardcoded Guides (Fallback-2) [if Dynamic fails]     │
│    ├─ AZ-204, AZ-400, DP-203, AZ-900 built-in                   │
│    └─ Prevents complete failure                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Return Format** (Foundry IQ):
```python
{
  "content": "Full exam guide...",
  "citations": [
    "https://learn.microsoft.com/azure-sdk-101",
    "https://docs.microsoft.com/azure-functions-guide"
  ],
  "source": "Foundry IQ"  # Used for transparency badge in UI
}
```

**Feature Flag**: `USE_FOUNDRY_IQ=true` in .env controls plugin selection:
- `true` → FoundryKnowledgePlugin (recommended for production)
- `false` → DynamicKnowledgePlugin (useful for development/testing)

---

## Environment Variables

```env
# === Azure OpenAI (LLM) ===
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-04-14

# === Azure AI Foundry IQ (Primary Knowledge) ===
# Feature flag: true = use Foundry IQ, false = use DynamicKnowledgePlugin
USE_FOUNDRY_IQ=true

# Foundry project settings (get from Azure Portal)
AZURE_FOUNDRY_PROJECT_NAME=certops-ai
AZURE_FOUNDRY_HUB=certops-ai-resource
AZURE_FOUNDRY_RESOURCE_GROUP=rg-arungajapathi-3294
AZURE_FOUNDRY_REGION=eastus
AZURE_FOUNDRY_KNOWLEDGE_BASE=certops-knowledge
AZURE_FOUNDRY_SEARCH_SERVICE=certopsaisrcho5ibpj

# Required for Foundry connection string construction
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_FOUNDRY_CONNECTION_STRING=  # Leave empty to auto-construct from components above

# === Database ===
DATABASE_PATH=./certops.db
```

---

## Foundry IQ Configuration — Quick Start

To enable Azure AI Foundry IQ as primary knowledge source:

1. **Get Subscription ID**:
   ```bash
   az account show --query id
   ```

2. **Add to .env**:
   ```env
   USE_FOUNDRY_IQ=true
   AZURE_SUBSCRIPTION_ID=<your-id>
   ```

3. **Verify Connection**:
   ```bash
   python scripts/find_connection_string.py
   ```

4. **Verify in Code**:
   ```python
   from backend.plugins.knowledge_router import get_knowledge_plugin
   plugin = get_knowledge_plugin()  # Returns FoundryKnowledgePlugin if enabled
   guide = plugin.get_certification_guide("AZ-204")
   print(guide["source"])  # Should be "Foundry IQ"
   ```

---

## Dynamic Certification Support

**Frontend** now accepts free-text certification input (no whitelist):
- Users type any certification name (e.g., "AZ-204", "AWS-SOA", "CKA")
- Backend converts to uppercase
- Knowledge retrieval uses cascading fallback chain

**Example Flow**:
1. User enters "AZ-204"
2. LearningAgent calls `get_knowledge_plugin().get_certification_guide("AZ-204")`
3. If Foundry IQ unavailable → tries web scraping → tries LLM → falls back to hardcoded
4. Returns guide with source attribution ("Foundry IQ" | "Dynamic Web" | "LLM Knowledge" | "Offline Fallback")
5. Streamlit displays corresponding badge (⚡ | 🌐 | 🤖 | 📚)
- **Transparency**: Memory includes `knowledge_source` to show which layer was used
- **Speed**: Offline fallback prevents timeouts

---

```
certops-ai/
├── PROJECT_CONTEXT.md          ← THIS FILE — always read first
├── README.md                   ← Hackathon submission README
├── .env.example
├── .gitignore
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── main.py                 ← FastAPI app
│   ├── database.py             ← SQLite init + queries
│   ├── memory.py               ← SharedMemory class
│   ├── orchestrator.py         ← Agent orchestration logic
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py       ← BaseAgent all agents inherit
│       ├── learning_agent.py
│       ├── study_plan_agent.py
│       ├── engagement_agent.py
│       ├── assessment_agent.py
│       ├── socratic_coach.py
│       ├── reflection_agent.py
│       ├── manager_insights.py
│       ├── reputation/
│       │   └── engine.py
│       └── council/
│           ├── __init__.py
│           ├── optimist.py
│           ├── skeptic.py
│           ├── advocate.py
│           ├── historian.py
│           ├── risk_analyst.py
│           └── critic.py
├── frontend/
│   └── app.py                  ← Streamlit UI — 7 pages
├── data/
│   ├── synthetic/
│   │   ├── learners.json
│   │   ├── work_signals.json
│   │   └── certifications.json
│   └── knowledge/
│       ├── az204_guide.md
│       ├── az400_guide.md
│       └── dp203_guide.md
└── docs/
    └── architecture.md
```

---

## Agent Roster — Complete List

| # | Agent | File | Role | Model | SK Plugin |
|---|---|---|---|---|---|
| 1 | Learning Agent | learning_agent.py | Query Foundry IQ, build skill map | GPT-4o | FoundryKnowledgePlugin |
| 2 | Study Plan Agent | study_plan_agent.py | Convert skills + time into week-by-week plan | GPT-4o | — |
| 3 | Engagement Agent | engagement_agent.py | Recommend study windows from work signals | GPT-4o | — |
| 4 | Optimist | council/optimist.py | Argues WHY learner CAN pass | GPT-4o | — |
| 5 | Skeptic | council/skeptic.py | Argues WHY learner WILL fail | GPT-4o | — |
| 6 | Advocate | council/advocate.py | Checks practical constraints — workload, stress | GPT-4o | — |
| 7 | Historian | council/historian.py | Finds similar past learners from SQLite | GPT-4o | HistoryPlugin |
| 8 | Risk Analyst | council/risk_analyst.py | Calculates topic coverage gaps + schedule risk | GPT-4o | — |
| 9 | Critic | council/critic.py | Synthesises 5 council votes using reputation weights | GPT-4o | ReputationPlugin |
| 10 | Assessment Agent | assessment_agent.py | Generates grounded mock questions + scores | GPT-4o | AssessmentPlugin |
| 11 | Socratic Coach | socratic_coach.py | Diagnoses misconceptions via guided questions | GPT-4o | — |
| 12 | Reflection Agent | reflection_agent.py | Compares prediction vs outcome, updates reputation | GPT-4o | ReputationPlugin |
| 13 | Manager Insights | manager_insights.py | Team readiness summary from SQLite | GPT-4o | — |

**Total: 13 agents. Do not add more without updating this file.**

---

## Semantic Kernel Plugins

| Plugin | File | Purpose | Used By |
|---|---|---|---|
| FoundryKnowledgePlugin | plugins/foundry_knowledge_plugin.py | **PRIMARY**: Query Azure AI Foundry IQ for certified, web-grounded content with citations. Cascades to DynamicKnowledgePlugin → Offline on failure. | Learning Agent |
| DynamicKnowledgePlugin | plugins/dynamic_knowledge_plugin.py | **FALLBACK-1**: Scrape MS Learn (5s timeout). Falls back to LLM generation. Caches results. | FoundryKnowledgePlugin (cascading) |
| knowledge_router.py | plugins/knowledge_router.py | **FACTORY**: Selects plugin based on `USE_FOUNDRY_IQ` env flag. Single import point. | All agents |
| HistoryPlugin | plugins/history_plugin.py | Find similar learners from SQLite history by certification/score/hours | Historian Agent |
| AssessmentPlugin | plugins/assessment_plugin.py | Generate questions + score answers | Assessment Agent |
| ReputationPlugin | plugins/reputation_plugin.py | Compute council voting weights from success rates | Critic Agent, Reflection Agent |

---

## Shared Memory Schema — FROZEN

```python
{
  "learner_id": "",           # string e.g. "L-1001"
  "role": "",                 # string e.g. "Cloud Engineer"
  "certification": "",        # string e.g. "AZ-204"
  "target_weeks": 0,          # int
  "skill_map": [],            # list of skill strings
  "knowledge_source": "",     # string: "Foundry IQ" | "Dynamic Web" | "LLM Knowledge" | "Offline Fallback"
  "citations": [],            # list of source URLs from Foundry IQ
  "recommended_materials": [], # list of {title, section, url}
  "study_plan": {},           # dict {week_1: [...], week_2: [...]}
  "work_signals": {},         # dict {meeting_hours, focus_hours, slot}
  "practice_score_avg": 0,    # float 0-100
  "hours_studied": 0,         # int
  "weak_topics": [],          # list of topic strings
  "exam_domains": [],         # list of {domain, weight_percent, key_topics}
  "council_votes": {},        # dict {agent_name: {verdict, confidence, evidence}}
  "readiness_verdict": "",    # READY | NOT_READY | DELAY
  "readiness_confidence": 0,  # float 0-100
  "readiness_reasoning": "",  # string — critic explanation
  "assessment_score": 0,      # float 0-100
  "assessment_breakdown": {}, # dict {topic: score}
  "assessment_outcome": "",   # PASS | FAIL
  "misconceptions": [],       # list of strings
  "socratic_questions": [],   # list of strings
  "reflection": {},           # dict {prediction, actual, analysis}
  "session_log": []           # list of log strings with timestamps
}
```

**All agents read from and write to this dict only. No direct agent-to-agent calls.**

---

## Database Schema — FROZEN (4 tables only)

```sql
-- Table 1
CREATE TABLE IF NOT EXISTS agent_reputation (
  agent_name TEXT PRIMARY KEY,
  accuracy_score REAL DEFAULT 75.0,
  total_predictions INTEGER DEFAULT 0,
  correct_predictions INTEGER DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT,
  certification TEXT,
  predicted_outcome TEXT,
  confidence REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 3
CREATE TABLE IF NOT EXISTS assessment_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT,
  certification TEXT,
  score REAL,
  topic_breakdown TEXT,
  outcome TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4
CREATE TABLE IF NOT EXISTS reflections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT,
  predicted_outcome TEXT,
  actual_outcome TEXT,
  analysis TEXT,
  agents_correct TEXT,
  agents_wrong TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Seed agent_reputation with: optimist, skeptic, advocate, historian, risk_analyst at 75.0 on init.**

---

## FastAPI Endpoints — FROZEN

| Method | Endpoint | Input | Output |
|---|---|---|---|
| POST | /learn | learner_id, role, certification, target_weeks | skill_map, study_plan |
| POST | /readiness | learner_id | council_votes, verdict, confidence |
| POST | /assessment | learner_id | score, topic_breakdown, outcome |
| POST | /coaching | learner_id | misconceptions, socratic_questions |
| POST | /reflection | learner_id, actual_outcome | accuracy, agents_correct, agents_wrong |
| POST | /pipeline | learner_id, role, certification, target_weeks | consolidated report with all 6 phases |
| POST | /adaptive | learner_id, max_iterations | iterations, final_outcome, final_score, history, study_plan, weak_topics |
| GET | /manager | — | team_readiness, at_risk, pass_rate |
| GET | /reputation | — | agent accuracy scores |
| GET | /health | — | status ok |
| GET | /state | — | current shared memory state |
| GET | /pipeline/status | — | phases_complete, progress_pct, current_phase, is_complete |

---

## Streamlit Pages — Redesigned

**PRIMARY FLOW (Main View):**

| Page | Name | Key Feature |
|---|---|---|
| 1 | Pipeline (Main) | ⭐ **PRIMARY** — Single-button automated pipeline. Input form + "Run Full Analysis" triggers all 6 phases sequentially with live progress. Results display as each phase completes. Consolidated report at end. No manual navigation required. |

**DEEP-DIVE VIEWS (Read-Only, Sidebar Navigation):**

| Page | Name | Key Feature |
|---|---|---|
| 2 | Council Debate | Live chat-style debate (left/right bubbles) + dramatic verdict reveal with SVG confidence ring. Read-only. |
| 3 | Manager Insights | Team-level readiness, at-risk learners, topic weakness patterns |
| 4 | Agent Reputation | Plotly bar chart of agent accuracy scores from all pipeline runs |
| 5 | Reasoning Trace | Full session log of all agent actions |

**KEY CHANGES FROM PREVIOUS VERSION:**
- Removed separate page buttons for Learning → Council → Assessment → Coaching flow
- Added single "Run Full Analysis" button that orchestrates all phases automatically
- Consolidated report replaces multi-page navigation as primary output
- Deep-dive pages moved to sidebar, are read-only (no execution buttons)
- Multi-page navigation still exists but only for inspection, not required for core flow

- **Language**: Python 3.11+
- **Async**: Use async/await throughout FastAPI. Streamlit calls FastAPI via httpx async client.
- **Agent pattern**: Every agent inherits BaseAgent. Every agent implements execute(memory: dict) -> dict.
- **LLM calls**: Always in _call_llm() method on BaseAgent. Never call OpenAI directly from agent logic.
- **Error handling**: Every LLM call wrapped in try/except. Return graceful fallback, never crash.
- **Logging**: Every agent calls _append_log(memory, message) to write to session_log.
- **Pydantic**: All FastAPI request/response bodies use Pydantic models.
- **No hardcoded responses**: Every agent makes a real LLM call. No fake/mock data in agent logic.
- **Synthetic data only**: All demo data uses fake IDs (L-1001, EMP-001). No real PII ever.
- **Secrets**: Never commit .env. Always use environment variables.

---

## Council Agent Output Schema

Every council agent returns this exact structure. Do not deviate:

```python
{
  "agent": "optimist",           # agent name string
  "verdict": "READY",            # READY | NOT_READY | DELAY
  "confidence": 82,              # int 0-100
  "evidence": [                  # list of 2-4 strings
    "Practice score trending up 3 weeks",
    "All high-weight domains above threshold"
  ],
  "recommendation": "Book exam within 5 days"  # one sentence
}
```

---

## Critic Agent Logic

```
1. Receive all 5 council votes
2. Load agent reputation weights from SQLite via ReputationPlugin
3. Weight each vote: weighted_confidence = vote.confidence * agent.accuracy_score
4. Tally weighted votes by verdict (READY / NOT_READY / DELAY)
5. Highest weighted tally wins
6. If margin < 15% — output DELAY regardless
7. Return: { verdict, confidence, reasoning, weighted_votes }
```

---

## Reputation Engine Logic

```
- All agents start at 75.0% accuracy
- After each assessment:
    Reflection Agent compares: council predicted X, actual outcome was Y
    For each agent: if prediction matched actual → correct_predictions += 1
    accuracy_score = (correct_predictions / total_predictions) * 100
- Critic uses current accuracy_score as weight when tallying council votes
- Higher accuracy = more influence on final verdict
```

---

## Foundry IQ Knowledge Base

Contents (markdown files loaded as context):
- az204_guide.md — AZ-204 study guide (synthetic)
- az400_guide.md — AZ-400 study guide (synthetic)  
- dp203_guide.md — DP-203 study guide (synthetic)

Every response from Learning Agent and Assessment Agent must cite:
- Source document name
- Section name
- Key finding

---

## What Is Built ✅ / In Progress 🔄 / Not Started ❌

| Component | Status | Notes |
|---|---|---|
| Folder structure | ✅ | Done |
| .env.example | ✅ | Done |
| requirements.txt | ✅ | Done |
| database.py | ✅ | Done |
| memory.py | ✅ | Done |
| base_agent.py | ✅ | Done |
| main.py (FastAPI) | ✅ | Stubs done |
| orchestrator.py | ✅ | Complete with run_full_pipeline(), _check_council_discrepancies(), _adapt_learning_plan(), _simulate_answers() |
| frontend/app.py | ✅ | Premium SaaS UI: hero section, glass cards, chat bubbles, animated SVG rings, stat cards, skill tags, circular progress — complete |
| POST /pipeline endpoint | ✅ | Complete with full 6-phase orchestration |
| GET /pipeline/status endpoint | ✅ | Complete for progress tracking |
| GET /state endpoint | ✅ | Memory inspection endpoint |
| GET /health endpoint | ✅ | System health check for sidebar indicator |
| Synthetic data files | ✅ | Done |
| Knowledge base guides | ✅ | Done |
| Learning Agent | ✅ | Basic skill-map generation implemented |
| Study Plan Agent | ✅ | Week-by-week planner implemented |
| Engagement Agent | ✅ | Work-signal based windows implemented |
| Council (5 agents) | ✅ | Optimist, Skeptic, Advocate, Historian, Risk Analyst — complete with parallel execution |
| Critic Agent | ✅ | Weighted vote synthesis with safety rules — complete |
| Assessment Agent | ✅ | Generates 10 exam questions, evaluates answers, saves to SQLite — complete |
| Socratic Coach | ✅ | Diagnoses misconceptions, generates Socratic questions, remediation plan — complete |
| POST /submit endpoint | ✅ | Submit answers, trigger coaching on FAIL — complete |
| Reflection Agent | ✅ | Self-learning analysis, updates agent reputations, saves to SQLite — complete |
| Reputation Engine | ✅ | SQLite-backed with update_reputation(), get_weights(), get_all_scores(), reset_to_defaults() — complete |
| Manager Insights Agent | ✅ | Team analytics, at-risk learners, topic weakness aggregation — complete |
| POST /reflection endpoint | ✅ | Reflection phase with reputation updates — complete |
| GET /manager endpoint | ✅ | Team insights endpoint — complete |
| GET /reset-demo endpoint | ✅ | Demo reset for reputation — complete |
| Streamlit Page 5 — Manager | ✅ | Team metrics, at-risk table, recent activity — complete |
| Streamlit Page 6 — Reputation | ✅ | Leaderboard with bars, reset button — complete |
| Streamlit Page 7 — Trace | ✅ | Agent execution log visualization — complete |
| All 7 Streamlit Pages | ✅ | Complete UI for entire system — FEATURE COMPLETE |
| Foundry IQ integration | ✅ | KnowledgePlugin with cascading fallback — complete |
| README final | ❌ | Day 8 |
| Demo video | ❌ | Day 8 |

---

## Explicit Constraints — Do NOT Do These

- ❌ Do not add more than 4 SQLite tables
- ❌ Do not add direct agent-to-agent communication
- ❌ Do not add real user data or PII
- ❌ Do not add authentication/login
- ❌ Do not add multi-tenant support
- ❌ Do not add Fabric IQ or Work IQ real integrations (roadmap only)
- ❌ Do not add OpenTelemetry (use Foundry tracing only)
- ❌ Do not add fine-tuning or model training
- ❌ Do not add a separate Knowledge Evolution Engine (roadmap)
- ❌ Do not hardcode LLM responses — every agent makes a real call
- ❌ Do not add new pages to Streamlit beyond the 7 defined
- ❌ Do not add new API endpoints beyond the 8 defined
- ❌ Do not change the shared memory schema without updating this file

---

## Roadmap (Post-Hackathon Only)

- Real Work IQ integration (calendar, meeting signals)
- Real Fabric IQ semantic layer
- Knowledge Evolution Engine (pattern learning)
- Multi-model council (DeepSeek R1, Claude, o1-mini per agent)
- Multi-tenant support
- Teams / Copilot integration via the FastAPI layer
- OpenTelemetry observability

---

## Changelog

| Date | Session | What Changed |
|---|---|---|
| 2026-06-09 | Session 1 | Initial project context created. Scaffold built. Architecture locked. |

---

## How To Use This File

**Before every coding session:**
Read this file top to bottom. Understand what's built. Understand what's next.

**Before writing any code:**
Check the constraints section. Check the frozen schemas. Do not deviate.

**After every coding session:**
Update the build status table. Add a changelog entry. Commit this file with your code.

**For any AI agent (Copilot, Windsurf, ChatGPT, Claude):**
Paste this file as context before giving any instruction. Say: "Read PROJECT_CONTEXT.md first. Then do the following task."

---

*CertOps AI — Built for Microsoft Agents League Hackathon 2026*
# 🧠 CertOps AI

### Self-Learning Certification Readiness Intelligence Platform

> **CertOps AI uses a council of specialized reasoning agents to assess certification readiness, challenges their conclusions through structured debate, diagnoses failures through Socratic coaching, and continuously improves future recommendations using a reputation-based learning system.**

<p align="center">

🏆 Microsoft Agents League Hackathon 2026
⚡ Reasoning Agents Track
☁ Azure AI Foundry + Foundry IQ
🤖 13 Specialized AI Agents
📈 Self-Learning Reputation Engine

</p>

<img width="1917" height="887" alt="CertOps-AI-Index" src="https://github.com/user-attachments/assets/7d7827af-c26a-46c5-ad0b-fdac8b12a70a" />

Live Demo

Demo URL

🌐 https://certops-ai.onrender.com

Deployment

- Frontend: Streamlit
- Backend: FastAPI
- Hosting: Render
- AI Services: Azure OpenAI

Notes

The application may take a few seconds to wake up if the Render instance has been idle.
---

# 🚀 Overview

CertOps AI is an enterprise-grade multi-agent reasoning platform designed to improve certification readiness through adversarial debate, grounded knowledge retrieval, certification-grade assessments, Socratic coaching, and continuous self-improvement.

Traditional learning platforms generate study plans and practice questions.

CertOps AI goes further.

It evaluates readiness through a council of specialist AI agents, challenges assumptions through structured reasoning, diagnoses misconceptions, learns from prediction failures, and continuously improves future recommendations.

---

# 🎯 The Problem

Organizations invest heavily in certification programs but continue to struggle with:

* Low certification pass rates
* Generic learning recommendations
* Lack of readiness visibility
* Repeated learning failures
* Poor understanding of root causes
* No mechanism for improving future recommendations

Most learning platforms answer:

> "What should I study?"

Very few answer:

> "Am I actually ready to pass?"

or

> "Why am I likely to fail?"

---

# 💡 The Solution

CertOps AI introduces a reasoning-first certification readiness system.

Instead of relying on a single AI opinion, multiple specialist agents independently evaluate readiness from different perspectives.

Their conclusions are debated, challenged, weighted, validated, and synthesized before a final recommendation is issued.

After assessments, the platform:

* Diagnoses misconceptions
* Explains failures
* Measures prediction quality
* Updates agent reputations
* Improves future recommendations

The result is a continuously improving intelligence system rather than a static learning platform.

---

# ✨ Key Innovations

## 🧠 Multi-Agent Readiness Council

Five specialist agents independently evaluate readiness.

| Agent        | Responsibility                               |
| ------------ | -------------------------------------------- |
| Optimist     | Identifies evidence supporting success       |
| Skeptic      | Identifies failure risks                     |
| Advocate     | Evaluates workload and practical constraints |
| Historian    | Compares against historical outcomes         |
| Risk Analyst | Assesses topic and schedule risk             |

---

## ⚖️ Critic Resolution Engine

The Critic Agent evaluates all council recommendations and produces:

* READY
* DELAY
* NOT READY

Along with:

* Confidence Score
* Supporting Evidence
* Risk Analysis
* Improvement Recommendations

---

## 📚 Azure AI Foundry IQ Grounding

Every recommendation is grounded using certification knowledge retrieved from Azure AI Foundry IQ.

Benefits:

* Reduced hallucination risk
* Explainable recommendations
* Source-backed guidance
* Certification-aligned content

---

## 🎓 Socratic Coaching

Instead of revealing answers directly, CertOps AI:

* Diagnoses misconceptions
* Uses guided questioning
* Encourages active recall
* Adapts remediation strategies

---

## 🔄 Reflection Engine

After assessments:

```text
Council Prediction
        vs
Actual Outcome
```

The Reflection Agent investigates:

* Why predictions succeeded
* Why predictions failed
* Which evidence mattered
* Which agents were accurate

---

## 📈 Reputation Engine

Every council agent receives an evolving accuracy score.

Example:

| Agent        | Accuracy |
| ------------ | -------- |
| Historian    | 91%      |
| Skeptic      | 88%      |
| Risk Analyst | 84%      |
| Advocate     | 79%      |
| Optimist     | 73%      |

Future decisions become more accurate as the system learns.

---

## 👨‍💼 Manager Intelligence

Provides organization-wide insights:

* Certification readiness
* At-risk learners
* Weak domains
* Readiness trends
* Learning effectiveness

---

# 🎬 Interactive User Journey

## 1️⃣ Create a Certification Mission

The learner enters:

```text
Role: Cloud Engineer
Certification: AZ-204
Target Timeline: 6 Weeks
```

CertOps AI creates a personalized readiness profile.

---

## 2️⃣ Build the Readiness Map

The Learning Agent analyzes:

* Certification objectives
* Existing skills
* Weak domains
* Study timeline

Example:

```text
Readiness Score: 68%

Strong Areas
✅ Azure Functions
✅ CI/CD

Risk Areas
⚠ Monitoring
⚠ Security
```

---

## 3️⃣ Generate a Personalized Study Plan

The Study Plan Agent creates a week-by-week roadmap.

```text
Week 1 → Azure Compute
Week 2 → Storage
Week 3 → Security
Week 4 → Monitoring
Week 5 → Practice Assessments
Week 6 → Final Revision
```

---

## 4️⃣ Watch the AI Council Debate

Five specialist agents independently evaluate readiness.

### Optimist

> Practice scores are improving rapidly. The learner is trending toward success.

### Skeptic

> Networking remains below readiness threshold.

### Advocate

> Workload pressure may impact retention.

### Historian

> Similar learners historically achieved only a 63% pass rate.

### Risk Analyst

> Monitoring objectives remain under-covered.

---

## 5️⃣ Critic Verdict

The Critic Agent synthesizes all opinions.

Example:

```text
Verdict: DELAY

Confidence: 84%

Reasoning:
• Monitoring coverage insufficient
• Historical failure probability elevated
• Schedule risk remains high
```

Every verdict is explainable.

---

## 6️⃣ Certification Assessment

The Assessment Agent generates certification-style mock exams.

Example:

```text
Overall Score: 74%

Compute ............ 85%
Storage ............ 78%
Security ........... 61%
Monitoring ......... 55%
```

---

## 7️⃣ Socratic Coaching

Instead of showing answers immediately:

```text
Why did you select Azure Functions?

What assumption influenced your decision?

How would your answer change if state persistence was required?
```

The goal is to uncover misconceptions rather than memorization gaps.

---

## 8️⃣ Reflection & Learning

The Reflection Agent compares:

```text
Prediction: PASS

Actual Outcome: FAIL
```

The system investigates:

* Why the prediction failed
* Which evidence was misleading
* Which agents were correct
* Which agents require recalibration

---

## 9️⃣ Reputation Update

Agent performance is updated automatically.

```text
Historian Agent ..... 91%
Skeptic Agent ....... 88%
Risk Analyst ........ 84%
Advocate Agent ...... 79%
Optimist Agent ...... 73%
```

Future recommendations adapt accordingly.

---

## 🔟 Manager Dashboard

Managers receive organization-wide readiness insights.

```text
AZ-204 Readiness

Ready ............ 12
At Risk .......... 5
Not Ready ........ 3

Top Weak Domains

• Monitoring
• Networking
• Security
```

---

# 🏗 Architecture

```text
                         USER
                           │
                           ▼
                    Streamlit UI
                           │
                           ▼
                      FastAPI API
                           │
                           ▼
                 Agent Orchestrator
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
Azure AI Foundry     Shared Memory          SQLite
      │                    │                    │
      └────────────────────┼────────────────────┘
                           │

─────────────────────────────────────────────

Learning Agent
      │
      ▼
Study Plan Agent
      │
      ▼

READINESS COUNCIL

├── Optimist
├── Skeptic
├── Advocate
├── Historian
└── Risk Analyst

      │
      ▼

Critic Agent

      │
      ▼

Assessment Agent

      │
      ▼

Socratic Coach

      │
      ▼

Reflection Agent

      │
      ▼

Reputation Engine

      │
      ▼

Manager Insights
```

---

# 🤖 Agent Ecosystem

| Agent            | Purpose                             |
| ---------------- | ----------------------------------- |
| Learning Agent   | Builds certification skill map      |
| Study Plan Agent | Generates learning roadmap          |
| Engagement Agent | Finds optimal study windows         |
| Optimist         | Identifies success evidence         |
| Skeptic          | Identifies failure risks            |
| Advocate         | Evaluates practical constraints     |
| Historian        | Compares historical outcomes        |
| Risk Analyst     | Assesses readiness gaps             |
| Critic           | Produces final verdict              |
| Assessment Agent | Generates certification assessments |
| Socratic Coach   | Diagnoses misconceptions            |
| Reflection Agent | Learns from outcomes                |
| Manager Insights | Provides organizational analytics   |

**Total Agents: 13**

---

# 🔄 Continuous Intelligence Loop

```text
Learn
  ↓
Plan
  ↓
Debate
  ↓
Assess
  ↓
Coach
  ↓
Reflect
  ↓
Improve
  ↓
Learn Again
```

CertOps AI continuously improves both learner outcomes and its own decision quality.

---

# ⚡ Technology Stack

| Layer               | Technology                          |
| ------------------- | ----------------------------------- |
| Frontend            | Streamlit                           |
| Backend             | FastAPI                             |
| Agent Orchestration | Custom Multi-Agent Orchestrator     |
| AI Platform         | Azure AI Foundry                    |
| Knowledge Layer     | Foundry IQ                          |
| LLM                 | Azure OpenAI GPT-4o                 |
| Semantic Kernel     | Azure Service Integration Layer     |
| Database            | SQLite                              |
| Visualization       | Plotly                              |
| Configuration       | Python Dotenv                       |
| Deployment          | Streamlit Cloud + Azure App Service |

---

# 📁 Project Structure

```text
certops-ai/

├── backend/
│   ├── agents/
│   │   ├── council/
│   │   └── reputation/
│   ├── orchestrator.py
│   ├── database.py
│   ├── memory.py
│   └── main.py
│
├── frontend/
│   └── app.py
│
├── data/
│   ├── knowledge/
│   └── synthetic/
│
├── docs/
│
├── requirements.txt
├── PROJECT_CONTEXT.md
└── README.md
```

---

# 🚀 Quick Start

## Clone Repository

```bash
git clone https://github.com/arungajapathi-hash/CertOps-AI.git

cd CertOps-AI
```

## Create Virtual Environment

```bash
python -m venv .venv
```

## Activate Environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment

Create:

```text
.env
```

Example:

```env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o

USE_FOUNDRY_IQ=true

AZURE_SUBSCRIPTION_ID=
AZURE_FOUNDRY_PROJECT_NAME=
AZURE_FOUNDRY_RESOURCE_GROUP=
AZURE_FOUNDRY_REGION=
```

## Run Backend

```bash
uvicorn backend.main:app --reload
```

Backend:

```text
http://localhost:8000
```

## Run Frontend

```bash
streamlit run frontend/app.py
```

Frontend:

```text
http://localhost:8501
```

---

# 📊 Explainability & Observability

CertOps AI provides complete decision transparency.

### Council Debate View

* Agent opinions
* Supporting evidence
* Confidence scores

### Decision Trace

* Reasoning path
* Supporting rationale
* Evidence lineage

### Reputation Dashboard

* Agent accuracy
* Prediction quality
* System learning metrics

### Manager Insights

* Team readiness
* Weak domains
* Organizational risk trends

---

# 🏆 Hackathon Alignment

| Requirement             | Implementation                     |
| ----------------------- | ---------------------------------- |
| Reasoning Agents        | ✅ Multi-Agent Readiness Council    |
| Agent Orchestration     | ✅ Custom Orchestrator              |
| Grounded Knowledge      | ✅ Azure AI Foundry IQ              |
| Explainability          | ✅ Debate + Decision Trace          |
| Continuous Learning     | ✅ Reflection + Reputation Engine   |
| Enterprise Scenario     | ✅ Certification Readiness Platform |
| Production Architecture | ✅ FastAPI + Streamlit              |

---

# 🔮 Future Roadmap

* Microsoft Teams Integration
* Fabric IQ Integration
* Multi-Model Agent Council
* Enterprise SSO
* Multi-Tenant Support
* Workforce Readiness Analytics
* Adaptive Learning Intelligence
* Learning Pattern Detection

---

# 📜 License

MIT License

---

### Built with Azure AI Foundry, Foundry IQ, GPT-4o, FastAPI and Streamlit

### Microsoft Agents League Hackathon 2026

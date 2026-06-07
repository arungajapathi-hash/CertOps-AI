\# 🚀 CertOps AI



\### Self-Learning Certification Readiness Intelligence Platform



> \*\*Diagnose certification failure before it happens. Learn from every outcome.\*\*



\---



\## 🎯 Overview



CertOps AI is a multi-agent reasoning platform built to improve enterprise certification readiness through debate-driven evaluation, Socratic coaching, and self-improving decision intelligence.



Traditional learning systems generate study plans and practice questions.



CertOps AI goes further.



It evaluates readiness through a council of specialized AI agents, challenges assumptions, diagnoses misconceptions, measures prediction accuracy, and continuously improves future recommendations.



Built for the \*\*Microsoft Agents League Hackathon 2026\*\* using:



\* Azure AI Foundry

\* Foundry IQ

\* Microsoft Agent Framework

\* GPT-4o

\* FastAPI

\* Streamlit



\---



\# 💡 Problem



Organizations invest heavily in certification programs but still struggle with:



\* Low certification pass rates

\* Generic learning recommendations

\* Lack of readiness visibility

\* Poor understanding of failure causes

\* No feedback loop for improvement



Most learning platforms answer:



> "What should I study?"



Very few answer:



> "Am I actually ready?"



or



> "Why am I likely to fail?"



\---



\# ✅ Solution



CertOps AI introduces a multi-agent readiness evaluation system.



Instead of relying on a single AI opinion, multiple specialized agents independently analyze readiness from different perspectives.



Their conclusions are challenged, debated, validated, and resolved before a final recommendation is made.



After assessments, the platform:



\* Diagnoses misconceptions

\* Reflects on prediction accuracy

\* Updates agent reputations

\* Improves future recommendations



\---



\# ✨ Key Features



\## 🧠 Multi-Agent Readiness Council



Five independent agents evaluate certification readiness.



| Agent        | Responsibility                               |

| ------------ | -------------------------------------------- |

| Optimist     | Finds evidence supporting success            |

| Skeptic      | Identifies failure risks                     |

| Advocate     | Evaluates workload and practical constraints |

| Historian    | Compares against historical outcomes         |

| Risk Analyst | Assesses topic and schedule risk             |



\---



\## ⚖️ Critic Resolution Engine



The Critic Agent reviews all council recommendations and produces:



\* Ready

\* Delay Exam

\* Not Ready



Along with:



\* Confidence Score

\* Evidence Summary

\* Improvement Recommendations



\---



\## 🎓 Socratic Coaching



Instead of revealing answers directly, CertOps AI:



\* Identifies misconceptions

\* Uses guided questioning

\* Encourages active recall

\* Adapts learning strategies



\---



\## 🔄 Reflection Engine



After assessments:



```text

Prediction

&#x20;       vs

Actual Outcome

```



The Reflection Agent investigates:



\* Why predictions succeeded

\* Why predictions failed

\* Which evidence mattered most



\---



\## 📈 Reputation Engine



Every council agent receives an accuracy score.



Example:



| Agent        | Accuracy |

| ------------ | -------- |

| Historian    | 91%      |

| Skeptic      | 87%      |

| Risk Analyst | 84%      |

| Optimist     | 72%      |



Future decisions become more accurate over time.



\---



\## 👥 Manager Intelligence



Provides team-level insights:



\* Certification readiness

\* At-risk learners

\* Weak skill areas

\* Readiness trends



\---



\# 🎬 Interactive User Journey



\## 1️⃣ Create a Certification Mission



The learner enters:



```text

Role: DevOps Engineer

Target Certification: AZ-400

Target Date: 6 Weeks

```



CertOps AI creates a personalized readiness profile.



\---



\## 2️⃣ Explore Your Readiness Map



The platform analyzes:



\* Skills

\* Certification objectives

\* Time constraints

\* Historical outcomes



Example:



```text

Readiness Score: 67%



Strong Areas

✅ CI/CD

✅ GitHub Actions



Risk Areas

⚠ Monitoring

⚠ Networking

```



\---



\## 3️⃣ Watch the AI Council Debate



Five specialist agents independently review readiness.



\### Optimist Agent



> Practice scores are improving rapidly. The learner is trending toward success.



\### Skeptic Agent



> Networking remains below threshold. This is a significant certification risk.



\### Advocate Agent



> Meeting load is high. Retention risk is increasing.



\### Historian Agent



> Similar learners historically achieved a 63% pass rate.



\### Risk Analyst



> Monitoring objectives remain under-covered.



\---



\## 4️⃣ Critic Verdict



The Critic Agent evaluates every argument.



Example:



```text

Verdict: Delay Exam



Confidence: 82%



Reasoning:

• Networking readiness below target

• Monitoring coverage incomplete

• Historical failure risk elevated

```



Every recommendation is explainable.



\---



\## 5️⃣ Take a Grounded Assessment



The Assessment Agent generates certification questions using Foundry IQ.



Results:



```text

Overall Score: 71%



CI/CD ............. 86%

Monitoring ........ 58%

Networking ........ 52%

```



\---



\## 6️⃣ Experience Socratic Coaching



Instead of immediately showing answers:



```text

Why did you select Azure Functions?



What assumption influenced your decision?



How would the answer change if state persistence was required?

```



The goal is to uncover misconceptions.



\---



\## 7️⃣ Reflection \& Learning



The system compares:



```text

Prediction: PASS

Actual Result: FAIL

```



The Reflection Agent investigates why.



\---



\## 8️⃣ Reputation Update



Agent performance is updated automatically.



Example:



```text

Historian Agent ..... 91%

Skeptic Agent ....... 87%

Risk Analyst ........ 84%

Optimist Agent ...... 72%

```



Future recommendations adapt accordingly.



\---



\## 9️⃣ Manager Dashboard



Managers receive organization-wide readiness insights.



```text

AZ-400 Readiness



Ready ............ 12

At Risk .......... 5

Not Ready ........ 3



Top Weak Skills:

• Monitoring

• Networking

• Security

```



\---



\# 🏗 Architecture



```text

&#x20;                    USER

&#x20;                      │

&#x20;                      ▼

&#x20;               Streamlit UI

&#x20;                      │

&#x20;                      ▼

&#x20;                 FastAPI API

&#x20;                      │

&#x20;                      ▼

&#x20;             Agent Orchestrator

&#x20;                      │

&#x20;      ┌───────────────┼───────────────┐

&#x20;      │               │               │

&#x20;      ▼               ▼               ▼

&#x20; Foundry IQ      Shared Memory     SQLite

&#x20;      │               │               │

&#x20;      └───────────────┼───────────────┘

&#x20;                      │



─────────────────────────────────────────────



Learning Agent

&#x20;      │

&#x20;      ▼

Study Plan Agent

&#x20;      │

&#x20;      ▼



READINESS COUNCIL



├── Optimist Agent

├── Skeptic Agent

├── Advocate Agent

├── Historian Agent

└── Risk Analyst Agent



&#x20;      │

&#x20;      ▼



Critic Agent



&#x20;      │

&#x20;      ▼



Assessment Agent



&#x20;      │

&#x20;┌─────┴─────┐

&#x20;│           │

PASS       FAIL

&#x20;│           │

&#x20;│           ▼

&#x20;│    Socratic Coach

&#x20;│

&#x20;▼

Reflection Agent

&#x20;│

&#x20;▼

Reputation Engine

&#x20;│

&#x20;▼

Manager Insights

```



\---



\# 🔄 Continuous Intelligence Loop



```text

Learn

&#x20; ↓

Debate

&#x20; ↓

Assess

&#x20; ↓

Coach

&#x20; ↓

Reflect

&#x20; ↓

Improve

&#x20; ↓

Learn Again

```



CertOps AI continuously improves both learner outcomes and its own decision quality.



\---



\# 🧩 Technology Stack



| Layer           | Technology                |

| --------------- | ------------------------- |

| Frontend        | Streamlit                 |

| Backend         | FastAPI                   |

| Agent Framework | Microsoft Agent Framework |

| AI Platform     | Azure AI Foundry          |

| LLM             | GPT-4o                    |

| Knowledge Layer | Foundry IQ                |

| Database        | SQLite                    |

| Visualization   | Plotly                    |

| Data Processing | Pandas                    |

| Configuration   | Python Dotenv             |



\---



\# 📁 Project Structure



```text

certops-ai/



backend/

├── agents/

│   ├── council/

│   └── reputation/

├── database.py

├── memory.py

├── orchestrator.py

└── main.py



frontend/

└── app.py



data/

├── knowledge/

└── synthetic/



docs/

```



\---



\# 🚀 Quick Start



\### Clone Repository



```bash

git clone <repository-url>

cd certops-ai

```



\### Create Virtual Environment



```bash

python -m venv .venv

```



\### Activate Environment



Windows



```bash

.venv\\Scripts\\activate

```



Linux / macOS



```bash

source .venv/bin/activate

```



\### Install Dependencies



```bash

pip install -r requirements.txt

```



\### Configure Environment



Create:



```text

.env

```



Example:



```env

AZURE\_OPENAI\_ENDPOINT=

AZURE\_OPENAI\_API\_KEY=

AZURE\_OPENAI\_DEPLOYMENT=

AZURE\_FOUNDRY\_PROJECT=

```



\### Run Backend



```bash

uvicorn backend.main:app --reload

```



Backend:



```text

http://localhost:8000

```



\### Run Frontend



```bash

streamlit run frontend/app.py

```



Frontend:



```text

http://localhost:8501

```



\---



\# 📊 Observability



CertOps AI provides full reasoning transparency.



\### Agent Execution Timeline



Track:



\* Execution Time

\* Status

\* Confidence

\* Latency



\### Council Debate View



Visualize:



\* Agent opinions

\* Supporting evidence

\* Confidence scores



\### Decision Trace



Understand:



\* Why a verdict was generated

\* Which evidence influenced decisions



\### Reputation Dashboard



Monitor:



\* Agent accuracy

\* Prediction quality

\* System improvement over time



\---



\# 🛣 Roadmap



Future enhancements:



\* Microsoft 365 Work IQ integration

\* Fabric IQ semantic layer

\* Teams integration

\* Enterprise authentication

\* Multi-tenant support

\* Advanced evaluation framework

\* Real enterprise learning analytics

\* Adaptive intervention simulator



\---



\# 🏆 Hackathon Alignment



\### Microsoft IQ Integration



✅ Foundry IQ



\### Multi-Agent Reasoning



✅ Readiness Council



\### Observability



✅ Debate View + Decision Trace



\### Continuous Learning



✅ Reflection + Reputation Engine



\### Enterprise Scenario



✅ Certification Readiness Intelligence



\---



\# 📜 License



MIT License



\---



\### Built with Azure AI Foundry, Foundry IQ and Microsoft Agent Framework


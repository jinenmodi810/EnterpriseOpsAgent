# 🚀 Enterprise Ops Agent  
**AI-powered Incident RCA (Root Cause Analysis) & Prevention Platform**

---

## 📘 Overview

Enterprise Ops Agent automates **incident root-cause analysis** and **proactive prevention** for DevOps and SRE teams.  
It ingests raw logs, correlates events using rule-based logic and **Gemini 1.5 Flash**, and produces **explainable RCA reports** with actionable recommendations.

Outputs are visualized through a **Next.js dashboard** featuring:

- Timeline
- Hypotheses
- Narrative
- Recommendations
- Calibration
- Causal Graph
- Similar Incidents

---

## 💡 Problem Statement

Enterprise support teams spend hours manually connecting alerts, metrics, and logs to find what truly caused an outage.  
Root Cause Analysis (RCA) is time-consuming, error-prone, and lacks explainability.  
As systems scale, manual triage simply doesn’t keep up.

**Pain Points:**

- Alert fatigue due to multiple monitoring tools  
- Long RCA cycles with inconsistent conclusions  
- Lack of unified and explainable postmortems  

---

## 🧠 Solution

Enterprise Ops Agent functions as an **autonomous RCA co-pilot** that:

1. **Ingests structured/unstructured logs** (CSV, JSON, API)  
2. **Builds a chronological timeline** of incident events  
3. **Applies hybrid reasoning** — rule-based + Gemini LLM  
4. **Generates confidence-calibrated RCA explanations**  
5. **Outputs recommendations and post-incident summaries**

---

## 🏗️ Architecture

```text
                ┌──────────────────────────────┐
                │        Frontend (Next.js)    │
                │   Upload Logs + Dashboard UI │
                └──────────────┬───────────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │   FastAPI Server  │
                     └───────────────────┘
                               │
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                              RCA Agents Layer                                │
 │ ┌──────────────────────────────────────────────────────────────────────────┐ │
 │ │ Ingestion Agent  →  Timeline Agent  →  Root Cause Agent (Gemini LLM)     │ │
 │ │   ↳ Calibration Agent → Similarity Agent → Narrative Agent →             │ │
 │ │   Recommendation Agent → Causal Graph Agent                              │ │
 │ └──────────────────────────────────────────────────────────────────────────┘ │
 └──────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                     JSON Response → React Dashboard


Backend Stack: Python 3.11 · FastAPI · Pandas · Gemini 2.5 Flash
Frontend Stack: Next.js 14 · TypeScript · Tailwind CSS
Runtime: FastAPI (uvicorn main:app --reload) + Next.js dev server


⚙️ Setup & Execution

### 1️⃣ Clone Repository
```bash
git clone https://github.com/jinenmodi810/EnterpriseOpsAgent.git
cd EnterpriseOpsAgent


2️⃣ Backend Setup (FastAPI + Gemini RCA Engine)

cd backend
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload


Backend API available at:
👉 http://127.0.0.1:8000

Test it quickly:

curl -X 'POST' \
'http://127.0.0.1:8000/api/v1/analyze/' \
-F 'file=@data/sample_incident.csv'


3️⃣ Frontend Setup (Next.js Dashboard)
cd frontend
npm install
npm run dev

🌐 Integration Potential

Integrations supported:
- Datadog / CloudWatch → Live log streams  
- ServiceNow / PagerDuty → Ticketing automation  
- Snowflake / BigQuery → RCA data storage  

These allow real-time ingestion and correlation across infrastructure and application layers.


🚀 Future Enhancements
- Real-time WebSocket streaming  
- Slack / Teams notification integration  
- Continuous learning using Gemini Pro  
- RCA pattern similarity for proactive prevention  
- Dockerized deployment with Helm support  


🧠 Learning Highlights
- Applied multi-agent orchestration for RCA reasoning  
- Combined rule-based and LLM logic (Gemini 2.5 Flash)  
- Built a modular, explainable AI Ops system  
- Deployed a full-stack RCA dashboard using FastAPI + Next.js  


🧰 Tech Stack

| Layer | Technology |
|-------|-------------|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Pandas |
| AI / LLM | Gemini 2.5 Flash |
| Visualization | Chart.js / D3 |
| Runtime | Uvicorn + Node.js 18 |
| Deployment | Docker, Localhost |


💎 Value Proposition
Enterprise Ops Agent reduces RCA time from hours to minutes,  
unifies logs, alerts, and incidents, and delivers explainable AI-driven analysis.  

Its modular architecture scales easily and integrates with enterprise observability tools.

📊 Example Output
{
  "severity": "critical",
  "primary_cause": "Downstream dependency or external service failure",
  "category": "customer-impact",
  "confidence": 0.23,
  "recommendations": [
    "Restart dependent payments-service container",
    "Scale checkout-api from 3 → 6 pods",
    "Schedule post-incident review"
  ]
}

🧪 Validation & Testing
✅ LLM Commentary (Gemini) → Confirms causal chain & mitigation  
✅ Calibration Layer → Adjusts scores via probabilistic normalization  
✅ Causal Graph Agent → Maps root-to-impact dependency chains  

🧭 Architecture Summary Diagram


+------------------------------------------------------+
|                   Enterprise Ops Agent               |
|------------------------------------------------------|
|  FastAPI Backend  |  Gemini RCA Engine               |
|  Ingestion Agent  |  Timeline Agent                  |
|  Root Cause Agent |  Recommendation Agent            |
|  Causal Graph     |  Calibration & Narrative Agents  |
|------------------------------------------------------|
|  Next.js Frontend Dashboard                          |
|  Upload CSVs · Visualize RCA · Explore Insights      |
+------------------------------------------------------+

🧠 Learning Impact
- Reduced RCA fatigue for engineering teams  
- Brought explainable AI to incident management  
- Scalable across enterprise observability stacks  


📜 License

Released under the Attribution 4.0 International (CC BY 4.0) license.  
© 2025 Jinen Modi — All Rights Reserved.
# InsightStream: Secure Autonomous Multi-Agent BI Pipeline
### Kaggle AI Agents Capstone Submission — Track: Agents for Business

InsightStream is an enterprise-grade agentic Business Intelligence (BI) portal designed to execute autonomous analysis pipelines on complex multi-month time-series data (MRR tracking, active user velocities, and API usage metrics). 

By separating analytical responsibilities through a rigid **DIG (Description, Introspection, Goal-Setting) Framework**, it shields business relational data layers behind an unbreakable, dual-layer database security sandbox, delivering 100% mathematically deterministic and human-replicable portfolios.

---

## System & Security Architecture

The framework coordinates a sequential pipeline of three specialized AI agents mapped directly to enterprise data team roles, enforcing strict data verification at every handoff interface.

```text
  [ Plain-Text Business Query ]
               │
               ▼
┌──────────────────────────────┐
│  1. Product Manager Agent    │  ◄── Goal-Setting & Strategic Milestones
└──────────────────────────────┘
               │
               ▼ Structured Execution Plan
┌──────────────────────────────┐
│   2. Data Engineer Agent     │  ◄── Dual-Layer Sandbox Schema Introspection
└──────────────────────────────┘
               │
               ▼ Secure Data Payload (JSON)
┌──────────────────────────────┐
│    3. Data Analyst Agent     │  ◄── Quantitative Calculations & Portfolio Export
└──────────────────────────────┘
               │
               ▼
   [ Generated BI Portfolio ]
```

### The DIG Framework Lifecycle

1. **Product Manager Agent (BI Lead)** ➔ *Goal-Setting*: Translates natural business prompts into clear mathematical target constraints, establishing business definitions before raw data queries are initialized.
2. **Data Engineer Agent (SQL Guard)** ➔ *Description & Introspection*: Audits column schemas, checks data availability constraints, and translates plans into highly optimized Text-to-SQL statements.
3. **Data Analyst Agent (Reproducibility Lead)** ➔ *Quantitative Matrix Execution*: Ingests payloads into standard math arrays (`pandas`), runs business health metrics, handles baseline anomalies, and exports isolated, immutable business reporting portfolios.

---

## Defense-in-Depth Security Perimeter

To prove data protection safety across live enterprise environments, InsightStream isolates the database connection layer inside an airtight **two-layer sandboxing system** that completely blocks unauthorized modifications:

* **Layer 1: Prior-to-Connection Static Filter:** Queries pass through case-insensitive regular expression boundaries (`\b...\b`) that immediately identify and strip malicious injections or destructive syntax (`INSERT`, `UPDATE`, `DROP`, `DELETE`, `PRAGMA`).
* **Layer 2: Engine-Level Connection Authorizer:** As a final defense-in-depth policy, a dynamic compilation callback is registered via `sqlite3.Connection.set_authorizer`. If a prompt bypasses the regex scanner, the underlying database core intercepts the machine bytecode at compile time, rejecting unauthorized transactions.

---

## Eliminating the LLM "Black Box": Deterministic Traceability

InsightStream natively resolves the problem of unpredictable AI hallucinations. Alongside markdown text summaries, the pipeline automatically exports a standalone **Human Verification Script (`replicate_analysis.py`)**.

Any data practitioner or manager can run this isolated Python script independently to hit the database using standard deterministic logic—yielding matching figures down to the penny for complete corporate auditing and compliance.

---

## Interactive Web Portal Interface

The dashboard includes a premium interactive management layer built natively with **Streamlit** (`ui_app.py`).

* **Live Monitoring Loops:** Uses synchronous status indicators to stream live execution state logs as context flows through the agent squad.
* **Platform Pipe Safety:** Equipped with a native `SafeStream` stream interceptor class preventing Windows terminal/NamedPipe disruptions (`WinError 233` / Broken Pipes).
* **Adaptive Chart Renders:** Automatically executes dynamic in-memory data pivots to render interactive charts alongside the downloadable portfolio artifacts.

---

## Getting Started Locally

### Prerequisites

* Python 3.8+
* Required Libraries: `pip install streamlit pandas matplotlib`

### Setup Commands

1. **Initialize and Seed the Warehouse:**
```bash
python setup_mock_db.py
```

2. **Launch the Web Interface:**
```bash
streamlit run ui_app.py
```

3. **Execute via CLI Pipeline (Alternative):**
```bash
python run_team.py
```

---

## Regression Testing Matrix

A comprehensive automated test suite is provided to verify security restrictions and database constraints:

```bash
python -m unittest test_db_tools.py
```

The test assertions validate schema extractions, syntax exception capturing, word-boundary regex exclusions, and connection authorizer sandbox rejections against adversarial bypass attempts.

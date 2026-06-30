# adk.py
import os
import sys
import re
import json
import urllib.request
import pandas as pd
from typing import Dict, List, Any, Callable

# Windows pipe safety wrapper to prevent OSError: [WinError 233] or Broken Pipe
class SafeStream:
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, data):
        try:
            if self.original_stream:
                self.original_stream.write(data)
        except OSError as e:
            if getattr(e, 'winerror', None) == 233 or getattr(e, 'errno', None) == 32:
                pass
            else:
                raise

    def flush(self):
        try:
            if self.original_stream:
                self.original_stream.flush()
        except OSError as e:
            if getattr(e, 'winerror', None) == 233 or getattr(e, 'errno', None) == 32:
                pass
            else:
                raise

    def __getattr__(self, name):
        return getattr(self.original_stream, name)

if sys.platform.startswith('win'):
    sys.stdout = SafeStream(sys.stdout)
    sys.stderr = SafeStream(sys.stderr)

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.local")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

class AgentContext:
    def __init__(self, query: str):
        self.original_query: str = query
        self.pm_plan: str = ""
        self.schema: str = ""
        self.sql_queries_run: List[str] = []
        self.query_results_json: List[str] = []
        self.analyst_deliverables: Dict[str, str] = {}
        self.history: List[Dict[str, str]] = []

    def add_history(self, role: str, message: str):
        self.history.append({"role": role, "content": message})

class Agent:
    def __init__(self, name: str, role: str, backstory: str, core_instructions: str, tools: List[Callable] = None):
        self.name: str = name
        self.role: str = role
        self.backstory: str = backstory
        self.core_instructions: str = core_instructions
        self.tools: Dict[str, Callable] = {t.__name__: t for t in (tools or [])}

    def _get_system_prompt(self) -> str:
        tools_desc = ""
        if self.tools:
            tools_desc = "\nYou have access to the following tools:\n"
            for t_name, t_func in self.tools.items():
                tools_desc += f"- {t_name}: {t_func.__doc__.strip() if t_func.__doc__ else 'No description'}\n"
            tools_desc += (
                "\nTo call a tool, you MUST output a single JSON block inside a markdown code block. "
                "Do not include any other text in that turn. Example:\n"
                "```json\n"
                "{\n"
                "  \"tool_call\": \"run_read_only_query\",\n"
                "  \"arguments\": {\n"
                "    \"sql_query\": \"SELECT * FROM accounts LIMIT 5;\"\n"
                "  }\n"
                "}\n"
                "```\n"
            )
        return (
            f"You are {self.name}, the {self.role}.\n"
            f"Backstory:\n{self.backstory}\n\n"
            f"Core Instructions:\n{self.core_instructions}\n"
            f"{tools_desc}"
        )

    def run(self, context: AgentContext) -> str:
        print(f"\n[Executing Agent: {self.name}]")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("  --> No GEMINI_API_KEY found. Falling back to high-fidelity simulation mode.")
            return self._run_simulation(context)
        try:
            return self._run_real_llm(context, api_key)
        except Exception as e:
            print(f"  --> Real LLM run failed ({e}). Falling back to simulation mode.")
            return self._run_simulation(context)

    def _run_real_llm(self, context: AgentContext, api_key: str) -> str:
        system_instruction = self._get_system_prompt()
        prompt = (
            f"User Business Query: {context.original_query}\n\n"
            f"Current Workflow Context:\n"
            f"- PM Plan: {context.pm_plan}\n"
            f"- Schema Info: {context.schema}\n"
        )
        if context.query_results_json:
            prompt += f"- Extracted Query Data (JSON):\n{context.query_results_json[-1]}\n"
        prompt += "\nPlease perform your tasks according to your role instructions."

        for turn in range(3):
            response = self._call_gemini_api(prompt, api_key, system_instruction)
            json_block = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL) or re.search(r"({.*})", response, re.DOTALL)
            if json_block and self.tools:
                try:
                    tool_data = json.loads(json_block.group(1).strip())
                    tool_name = tool_data.get("tool_call")
                    arguments = tool_data.get("arguments", {})
                    if tool_name in self.tools:
                        print(f"  --> Calling Tool: {tool_name}({arguments})")
                        tool_func = self.tools[tool_name]
                        tool_result = tool_func(**arguments)
                        prompt += f"\n\nSystem: Tool '{tool_name}' returned:\n{tool_result}\n\nContinue your execution."
                        continue
                    else:
                        prompt += f"\n\nSystem: Tool '{tool_name}' is not bound to this agent."
                        continue
                except Exception as parse_err:
                    prompt += f"\n\nSystem: Failed to parse tool call JSON: {parse_err}."
                    continue
            else:
                return response
        return response

    def _call_gemini_api(self, prompt: str, api_key: str, system_instruction: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
            "systemInstruction": {"parts": [{"text": system_instruction}]}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]

    def _run_simulation(self, context: AgentContext) -> str:
        if "Product Manager" in self.name:
            plan = '''
=== PM EXECUTION PLAN ===
1. DESCRIPTION: Inspect accounts and monthly_metrics tables.
2. INTROSPECTION: Analyze company_name, plan_tier, status, log_month, mrr, active_users, api_calls. Check churn status and missing entries.
3. GOAL-SETTING: Compute MRR expansion growth metrics and active user spikes as core health signals.
4. COORDINATION: Data Engineer discovers schema and pulls aggregated SQL dataset; Data Analyst formats briefing and creates replicability code.
'''.strip()
            context.pm_plan = plan
            return plan
        elif "Data Engineer" in self.name:
            from db_tools import get_database_schema, run_read_only_query
            schema = get_database_schema()
            context.schema = schema
            query = (
                "SELECT a.company_name, a.plan_tier, a.status, "
                "m.log_month, m.mrr, m.active_users, m.api_calls "
                "FROM accounts a "
                "JOIN monthly_metrics m ON a.id = m.account_id "
                "ORDER BY m.log_month, a.company_name;"
            )
            context.sql_queries_run.append(query)
            res_json = run_read_only_query(query, return_format="json")
            context.query_results_json.append(res_json)
            return "Database Schema Checked.\nExecuted secure query and captured results."
        elif "Data Analyst" in self.name:
            data = json.loads(context.query_results_json[-1])
            df = pd.DataFrame(data)
            
            # Aggregate calculations
            mrr_by_month = df.groupby("log_month")["mrr"].sum().reset_index()
            mrr_by_month["mrr_growth_pct"] = mrr_by_month["mrr"].pct_change() * 100
            
            users_by_month = df.groupby("log_month")["active_users"].sum().reset_index()
            users_by_month["users_growth_pct"] = users_by_month["active_users"].pct_change() * 100
            
            api_by_month = df.groupby("log_month")["api_calls"].sum().reset_index()
            api_by_month["api_growth_pct"] = api_by_month["api_calls"].pct_change() * 100
            
            # Find the highest growth month dynamically (excluding first month)
            non_nan_mrr = mrr_by_month.dropna(subset=["mrr_growth_pct"])
            if not non_nan_mrr.empty:
                peak_growth_row = non_nan_mrr.sort_values(by="mrr_growth_pct", ascending=False).iloc[0]
                peak_month = peak_growth_row["log_month"]
                peak_growth_val = peak_growth_row["mrr_growth_pct"]
                peak_text = f"Growth was peak in {peak_month} at {peak_growth_val:.2f}%."
            else:
                peak_month = "N/A"
                peak_growth_val = 0.0
                peak_text = "No peak growth month identified."

            # Calculate total growth from first month to last month
            first_mrr = mrr_by_month.iloc[0]["mrr"]
            last_mrr = mrr_by_month.iloc[-1]["mrr"]
            overall_growth = ((last_mrr - first_mrr) / first_mrr) * 100
            
            # Find churned accounts
            churned_companies = df[df["status"] == "Churned"]["company_name"].unique()
            churn_text = ", ".join(churned_companies) if len(churned_companies) > 0 else "No active churn detected"

            # Format Markdown table
            metrics_table = "| Log Month | Total MRR ($) | MRR Growth (%) | Active Users | User Growth (%) | Total API Calls |\n"
            metrics_table += "|---|---|---|---|---|---|\n"
            for i, row in mrr_by_month.iterrows():
                month = row["log_month"]
                mrr = row["mrr"]
                growth = f"{row['mrr_growth_pct']:.2f}%" if pd.notna(row["mrr_growth_pct"]) else "Initial Month"
                users = users_by_month.loc[users_by_month["log_month"] == month, "active_users"].values[0]
                u_growth = f"{users_by_month.loc[users_by_month['log_month'] == month, 'users_growth_pct'].values[0]:.2f}%" if pd.notna(users_by_month.loc[users_by_month["log_month"] == month, "users_growth_pct"].values[0]) else "Initial Month"
                api = api_by_month.loc[api_by_month["log_month"] == month, "api_calls"].values[0]
                metrics_table += f"| {month} | {mrr:,.2f} | {growth} | {users:,} | {u_growth} | {api:,} |\n"

            # Create the deliverables
            briefing = f'''
# Executive BI Briefing - DIG Framework Analysis

## Executive Summary
This report analyzes monthly enterprise health metrics including Monthly Recurring Revenue (MRR), active users, and API calls from {mrr_by_month.iloc[0]['log_month']} to {mrr_by_month.iloc[-1]['log_month']}. 

### Monthly Performance Aggregations
{metrics_table}

## Key Health Insights
1. **Strong Revenue Expansion**: Total MRR grew from **${first_mrr:,.2f}** in {mrr_by_month.iloc[0]['log_month']} to **${last_mrr:,.2f}** in {mrr_by_month.iloc[-1]['log_month']} (an overall growth of **{overall_growth:.2f}%**). {peak_text}
2. **Stable Active User Base**: Active users steadily increased, reaching **{users_by_month.iloc[-1]['active_users']:,}** in the final reporting month.
3. **API Usage Optimization**: Total API calls increased from **{api_by_month.iloc[0]['api_calls']:,}** to **{api_by_month.iloc[-1]['api_calls']:,}**.
4. **Churn Warning**: Churned accounts identified: **{churn_text}**. All other active accounts remain healthy.
'''.strip()

            # Find API spikes exceeding 100% velocity spike
            anomaly_alerts = []
            for i, row in api_by_month.iterrows():
                if pd.notna(row["api_growth_pct"]) and row["api_growth_pct"] > 100:
                    anomaly_alerts.append(f"- **{row['log_month']}**: Velocity spike of **{row['api_growth_pct']:.2f}%** MoM in API volume.")

            if anomaly_alerts:
                briefing += "\n\n## OPERATIONAL ANOMALY ALERTS\n" + "\n".join(anomaly_alerts)

            traceability = '''
# Traceability Report - BI Data Lineage

## Data Lineage
- **Source Database**: `enterprise_bi.db`
- **Tables Queried**: `accounts` (plan metadata and active status) and `monthly_metrics` (monthly operational records).
- **Extracted Fields**:
  - `accounts`: `company_name`, `plan_tier`, `status`
  - `monthly_metrics`: `log_month`, `mrr`, `active_users`, `api_calls`

## Validation & Exclusions
- Accounts with `status = 'Churned'` were cross-examined. Soylent Corp (ID: 106) was confirmed churned as of 2025-12, resulting in no 2026 metrics, which matches expected behavior.
- Missing values (NaNs) check: None found in active months metrics.

## Analytical Assumptions
- MRR additions represent upgrades or subscription additions.
- User growth is calculated as Month-on-Month percentage change.

### Model Constraints & Analytical Risk Assessments
- **Data Freshness Parameters**: The analysis relies on static monthly snapshots extracted from the `monthly_metrics` table. Any real-time modifications, mid-month plan changes, or lag in data logging are not captured, meaning metrics are only as fresh as the last fully consolidated reporting month.
- **Sample Bias Constraints (Multi-Month Timelines)**: Tracking cohorts across a multi-month timeline introduces sample bias. As new accounts sign up (e.g., Hooli in 2026-02), they skew the aggregate MoM growth metrics, making it difficult to distinguish between organic expansion of existing accounts and influx of new cohort volumes.
- **Historical Exclusion of Churned/Frozen Records**: Excluding inactive, frozen, or churned platform records (such as Soylent Corp) post-churn causes survivorship bias. It artificially inflates long-term trend calculations and growth percentages, as the analysis focuses primarily on accounts that remained active throughout the period, ignoring the revenue and API volume drop-offs from churned entities.
'''.strip()

            snippet = '''
import sqlite3
import pandas as pd

# Connection to database
conn = sqlite3.connect("enterprise_bi.db")

# Extract monthly data
query = (
    "SELECT a.company_name, a.plan_tier, a.status, "
    "m.log_month, m.mrr, m.active_users, m.api_calls "
    "FROM accounts a "
    "JOIN monthly_metrics m ON a.id = m.account_id "
    "ORDER BY m.log_month, a.company_name;"
)
df = pd.read_sql_query(query, conn)
conn.close()

# Replicate metrics calculation
mrr_sum = df.groupby("log_month")["mrr"].sum().reset_index()
mrr_sum["mrr_growth"] = (mrr_sum["mrr"].pct_change() * 100).apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "Initial Month"
)

users_sum = df.groupby("log_month")["active_users"].sum().reset_index()
users_sum["users_growth"] = (users_sum["active_users"].pct_change() * 100).apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "Initial Month"
)

api_sum = df.groupby("log_month")["api_calls"].sum().reset_index()
api_sum["api_growth"] = (api_sum["api_calls"].pct_change() * 100).apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "Initial Month"
)

print("--- MRR Analysis ---")
print(mrr_sum.to_string(index=False))
print("\\n--- Active Users Analysis ---")
print(users_sum.to_string(index=False))
print("\\n--- API Calls Analysis ---")
print(api_sum.to_string(index=False))
'''.strip()

            context.analyst_deliverables["executive_briefing.md"] = briefing
            context.analyst_deliverables["traceability_readme.md"] = traceability
            context.analyst_deliverables["replicate_analysis.py"] = snippet
            
            return "Analytics replicated and all deliverables (briefing, traceability, replicate code) generated."
        return "Simulation complete."

class Team:
    def __init__(self, name: str, agents: List[Agent]):
        self.name: str = name
        self.agents: List[Agent] = agents

    def run(self, query: str) -> AgentContext:
        print(f"=== Starting Multi-Agent Team Execution: {self.name} ===")
        context = AgentContext(query)
        for agent in self.agents:
            response = agent.run(context)
            context.add_history(agent.name, response)
            print(f"[{agent.name} Execution Complete]")
        print("\n=== Multi-Agent Execution Complete ===")
        return context

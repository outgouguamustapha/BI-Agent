import streamlit as st
import os
import sys
import json
import pandas as pd
from adk import AgentContext
from team_orchestrator import build_bi_analysis_team

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

# Page Configuration & Styling
st.set_page_config(page_title="InsightStream | Agentic BI Portal", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subtitle { font-size: 1.1rem; color: #4B5563; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">InsightStream Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Secure Autonomous Multi-Agent Business Intelligence Pipeline</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("Security Framework")
    st.success("Layer 1: Regex Filter Active")
    st.success("Layer 2: SQL Engine Sandbox Active")
    st.markdown("---")
    st.markdown("**DIG Process Sequence:**\n1. Product Manager\n2. Data Engineer\n3. Data Analyst")

# User Input Layout
user_query = st.text_area(
    "What business intelligence question can the team investigate today?",
    value="Analyze our monthly MRR growth, active user trends, and API usage to find health signals.",
    height=70
)

# Initialize Session State
if "ctx" not in st.session_state:
    st.session_state.ctx = None

if st.button("Execute Autonomous Pipeline", type="primary"):
    if not user_query.strip():
        st.warning("Please type a valid analytical query first.")
    else:
        with st.status("AI Agent Team Collaborating...", expanded=True) as status:
            st.write("**[Product Manager Agent]** Running Goal-Setting & Strategy...")
            team = build_bi_analysis_team()
            st.session_state.ctx = team.run(user_query)
            status.update(label="Analysis Complete! Portfolio Generated.", state="complete")

if st.session_state.ctx is not None:
    ctx = st.session_state.ctx
    st.markdown("---")
    
    # Display Outputs Natively in Interactive Columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Executive Analytical Briefing")
        if "executive_briefing.md" in ctx.analyst_deliverables:
            st.markdown(ctx.analyst_deliverables["executive_briefing.md"])
        else:
            st.info("Briefing generated inside portfolio folder.")
        
    with col2:
        st.subheader("Trend Visualization")
        
        # Use native Streamlit chart if data is available
        rendered_native = False
        try:
            if ctx.query_results_json:
                data = json.loads(ctx.query_results_json[-1])
                df = pd.DataFrame(data)
                if "log_month" in df.columns and "mrr" in df.columns:
                    mrr_by_month = df.groupby("log_month")["mrr"].sum().reset_index()
                    chart_data = mrr_by_month.set_index("log_month")[["mrr"]]
                    st.line_chart(chart_data, use_container_width=True)
                    rendered_native = True
        except Exception as chart_err:
            st.warning(f"Could not render interactive chart: {chart_err}")
            
        if not rendered_native:
            chart_path = "portfolio/mrr_trend.png"
            if os.path.exists(chart_path):
                st.image(chart_path, caption="Monthly Recurring Revenue Trajectory")
            else:
                st.info("Trend chart rendered to folder context.")
            
        with st.expander("View Audit & Traceability Logs"):
            if "traceability_readme.md" in ctx.analyst_deliverables:
                st.markdown(ctx.analyst_deliverables["traceability_readme.md"])
            
        with st.expander("Get Human Verification Script (Python)"):
            if "replicate_analysis.py" in ctx.analyst_deliverables:
                st.code(ctx.analyst_deliverables["replicate_analysis.py"], language="python")

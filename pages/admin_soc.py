import streamlit as st
import time
import random
from datetime import datetime
from local_llm_judge import LocalGuardrailJudge

# Initialize local judge for generating the incident reports
if 'soc_judge' not in st.session_state:
    st.session_state.soc_judge = LocalGuardrailJudge(use_mock=True)

st.set_page_config(page_title="SOC Admin - AI-WAF", page_icon="📡", layout="wide")

# Custom CSS for the SOC Dashboard
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .soc-header {
        color: #ff4444;
        font-family: 'Courier New', Courier, monospace;
        border-bottom: 2px solid #ff4444;
        padding-bottom: 10px;
    }
    .metric-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 5px;
        text-align: center;
    }
    .threat-red { color: #ff4444; font-weight: bold; }
    .threat-green { color: #2ea043; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='soc-header'>📡 ACTIVE DEFENSE: Security Operations Center</h1>", unsafe_allow_html=True)
st.write("Welcome, System Administrator. This dashboard monitors real-time Honeypot telemetry and generates AI-driven incident reports.")

# Quick stats
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='metric-box'>TOTAL ATTACKS CAUGHT<br><br><span style='font-size: 24px; color: #ff4444;'>" + str(len(st.session_state.get('sandbox_logs', []))) + "</span></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-box'>HONEYPOT STATUS<br><br><span style='font-size: 24px; color: #2ea043;'>ACTIVE</span></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-box'>AI RESPONSE ENGINE<br><br><span style='font-size: 24px; color: #58a6ff;'>ONLINE</span></div>", unsafe_allow_html=True)

st.markdown("---")

logs = st.session_state.get('sandbox_logs', [])

if not logs:
    st.info("No active threats detected in the Honeypot at this time. Monitoring network...")
else:
    st.subheader("🚨 Live Honeypot Telemetry & AI Incident Response")
    
    # Grab the latest log
    latest_attack = logs[-1]
    
    col_intel, col_trace = st.columns([2, 1])
    
    with col_intel:
        st.markdown(f"**Timestamp:** `{latest_attack['timestamp']}`")
        st.markdown(f"**Raw Attacker Payload:**\n```\n{latest_attack['attacker_input']}\n```")
        st.markdown(f"**Canary Token Served:**\n```json\n{latest_attack['honeypot_response']}\n```")
        
        # AI Incident Response Button
        if st.button("🧠 Generate AI Incident Report"):
            with st.spinner("Analyzing payload vectors via Local LLM..."):
                report = st.session_state.soc_judge.generate_incident_report(latest_attack['attacker_input'])
                
            st.success("Analysis Complete")
            st.markdown(f"""
            ### 🤖 Automated AI Analyst Report
            * **Threat Vector:** `{report['vector']}`
            * **Blast Radius:** `{report['damage_estimate']}`
            * **Recommended Action:** `{report['remedy']}`
            """)
            
    with col_trace:
        st.subheader("🌐 Forensic Traceback")
        if st.button("Initiate Traceback & Neutralize"):
            with st.spinner("Tracing connection..."):
                time.sleep(2)
                fake_ips = ["194.55.23.11 (Eastern Europe)", "45.22.19.8 (Unknown Proxy)", "112.90.3.4 (Data Center Node)"]
                trace = random.choice(fake_ips)
            
            st.error("Trace Complete")
            st.markdown(f"**Origin Detected:** `{trace}`")
            st.markdown("**Threat Actor Attribution:** `APT-Suspected`")
            st.markdown("<h3 style='color: #ff4444; border: 2px solid #ff4444; padding: 10px; text-align: center; border-radius: 5px;'>IP SUBNET BLOCKLISTED</h3>", unsafe_allow_html=True)
            st.write("Attacker neutralized. Honeypot reset.")

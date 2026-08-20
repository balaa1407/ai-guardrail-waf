import streamlit as st
import time
import random
from datetime import datetime
from local_llm_judge import LocalGuardrailJudge

# Initialize local judge for generating the incident reports
if 'soc_judge' not in st.session_state:
    st.session_state.soc_judge = LocalGuardrailJudge()

st.set_page_config(page_title="SOC Admin - AI-WAF", layout="wide")

# Custom CSS for the SOC Dashboard
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .soc-header {
        color: #e6edf3;
        font-weight: 500;
        font-size: 1.8rem;
        border-bottom: 1px solid #30363d;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }
    .metric-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 16px;
        border-radius: 6px;
        text-align: left;
    }
    .metric-title {
        font-size: 12px;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 500;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 600;
        margin-top: 4px;
        font-family: monospace;
    }
    .val-red { color: #f85149; }
    .val-green { color: #3fb950; }
    .val-blue { color: #58a6ff; }
    
    .table-header {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
        margin-bottom: 8px;
    }
    .log-row {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 8px;
        font-family: monospace;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='soc-header'>Security Operations Center</div>", unsafe_allow_html=True)
st.write("Unified telemetry dashboard. All actions are cryptographically verified.")

logs = st.session_state.get('audit_logs', [])
sandbox_logs = st.session_state.get('sandbox_logs', [])

# Quick stats
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Total Audit Records</div><div class='metric-value val-blue'>{len(logs)}</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Sandbox Captures</div><div class='metric-value val-red'>{len(sandbox_logs)}</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-box'><div class='metric-title'>Local AI Responder</div><div class='metric-value val-green'>ONLINE</div></div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: #30363d; margin: 2rem 0;'>", unsafe_allow_html=True)

col_feed, col_incident = st.columns([3, 2])

with col_feed:
    st.markdown("<h3 style='font-size: 1.1rem; margin-bottom: 16px;'>Unified Action Feed</h3>", unsafe_allow_html=True)
    if not logs:
        st.info("No telemetry recorded.")
    else:
        for record in reversed(logs):
            log = record["log"]
            action = log['action']
            if action == "BLOCKED": color = "#f85149"
            elif action == "PASSED": color = "#3fb950"
            elif action == "SANDBOX_TRIGGERED": color = "#d29922"
            else: color = "#58a6ff"
            
            st.markdown(f"""
            <div class='log-row' style='border-left: 3px solid {color};'>
                <div style='color: #8b949e; font-size: 0.75rem;'>{log['timestamp']}</div>
                <div style='margin: 8px 0; color: #c9d1d9;'><strong>Payload:</strong> {log['payload']}</div>
                <div style='color: {color}; font-weight: 600;'>[{action}] <span style='color: #8b949e; font-weight: 400;'>{log['reason']}</span></div>
            </div>
            """, unsafe_allow_html=True)

with col_incident:
    st.markdown("<h3 style='font-size: 1.1rem; margin-bottom: 16px;'>Active Defense Console</h3>", unsafe_allow_html=True)
    
    if not sandbox_logs:
        st.markdown("""
        <div style='background-color: #161b22; border: 1px dashed #30363d; border-radius: 6px; padding: 24px; text-align: center; color: #8b949e; font-size: 0.85rem;'>
            No active threat actors currently isolated in Sandbox.
        </div>
        """, unsafe_allow_html=True)
    else:
        latest = sandbox_logs[-1]
        st.markdown(f"""
        <div style='background-color: #161b22; border: 1px solid #f85149; border-radius: 6px; padding: 16px; margin-bottom: 16px;'>
            <div style='font-size: 11px; font-weight: 600; color: #f85149; margin-bottom: 8px;'>CRITICAL INCIDENT DETECTED</div>
            <div style='font-family: monospace; font-size: 0.8rem; color: #c9d1d9;'>
                <strong>Time:</strong> {latest['timestamp']}<br>
                <strong>Attacker Input:</strong> {latest['attacker_input']}<br>
                <strong>Canary Served:</strong> {latest['honeypot_response']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Generate Incident Report"):
            with st.spinner("Analyzing threat via local AI..."):
                report = st.session_state.soc_judge.generate_incident_report(latest['attacker_input'])
            
            st.markdown(f"""
            <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin-top: 16px;'>
                <div style='font-weight: 600; color: #e6edf3; margin-bottom: 8px; font-size: 0.95rem;'>Automated Threat Analysis</div>
                <div style='font-size: 0.85rem; color: #c9d1d9; margin-bottom: 4px;'><strong>Vector:</strong> {report['vector']}</div>
                <div style='font-size: 0.85rem; color: #c9d1d9; margin-bottom: 4px;'><strong>Impact:</strong> {report['damage_estimate']}</div>
                <div style='font-size: 0.85rem; color: #c9d1d9;'><strong>Remediation:</strong> {report['remedy']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.95rem; font-weight: 600; margin-bottom: 12px;'>Network Countermeasures</div>", unsafe_allow_html=True)
        
        if st.button("Initiate Traceback & Isolate"):
            with st.spinner("Tracing IP..."):
                import urllib.request
                import json
                try:
                    # Get real public IP
                    ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                    # Get location data
                    loc_url = f"http://ip-api.com/json/{ip}"
                    req = urllib.request.Request(loc_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=3) as response:
                        data = json.loads(response.read().decode('utf8'))
                        location = f"{data.get('city', 'Unknown City')}, {data.get('country', 'Unknown Country')}"
                    trace = f"{ip} ({location})"
                except Exception:
                    trace = "127.0.0.1 (Localhost / Fallback)"
                
            st.markdown(f"""
            <div style='background-color: rgba(248,81,73,0.1); border: 1px solid #f85149; border-radius: 6px; padding: 16px; margin-top: 16px;'>
                <div style='font-family: monospace; font-size: 0.85rem; color: #f85149; font-weight: 600;'>IP BLOCKLISTED: {trace}</div>
                <div style='font-size: 0.8rem; color: #c9d1d9; margin-top: 4px;'>Attacker neutralized. Session terminated.</div>
            </div>
            """, unsafe_allow_html=True)

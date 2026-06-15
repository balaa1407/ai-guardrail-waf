import streamlit as st
import os
import json
import re
import math

injection_patterns = [
    r"(?i)ignore\s+previous", 
    r"(?i)system\s+override", 
    r"(?i)developer\s+mode",
    r"(?i)bypass\s+filter"
]

def calculate_entropy(text):
    if not text:
        return 0.0
    entropy = 0.0
    for x in range(256):
        p_x = float(text.count(chr(x))) / len(text)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

def programmatic_pre_filter(text):
    for pattern in injection_patterns:
        if re.search(pattern, text):
            return False, "Heuristic Match: Unauthorized system override attempt detected."
            
    if len(text) > 30:
        entropy_score = calculate_entropy(text)
        if entropy_score > 5.2:
            return False, f"Anomaly Detection: High-entropy content ({entropy_score:.2f}) suspected of base64 obfuscation."
            
    return True, "Passed Ring 1 heuristic checks."

st.set_page_config(
    page_title="Enterprise AI Guardrail & WAF",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI Web Application Firewall (WAF)")
st.markdown("Intercepts, evaluates, and sanitizes LLM-generated text before it hits production.")

st.sidebar.header("Security Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model_select = st.sidebar.selectbox("Model Version", ["gemini-2.5-flash"])

col_main, col_audit = st.columns([2, 1])

with col_main:
    st.subheader("Simulate Incoming Payload")
    user_input = st.text_area("Paste draft marketing copy or prompt injection attack here:", height=150)
    
    run_scan = st.button("Run Security Scan")
    
    if run_scan:
        if not api_key:
            st.warning("Please enter your Gemini API Key in the sidebar.")
        elif not user_input:
            st.warning("Please enter text to scan.")
        else:
            st.info("Form validation complete. Ready to route payload through security rings.")

with col_audit:
    st.subheader("Cryptographic Audit Log")
    st.info("No audit logs available yet. Run a scan to see signed compliance records.")

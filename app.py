import streamlit as st
import os
import json
import re

injection_patterns = [
    r"(?i)ignore\s+previous", 
    r"(?i)system\s+override", 
    r"(?i)developer\s+mode",
    r"(?i)bypass\s+filter"
]

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

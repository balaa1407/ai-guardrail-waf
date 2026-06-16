import streamlit as st
import os
import json
import re
import math
import hmac
import hashlib
from datetime import datetime

# --- Ring 1: Heuristic Pre-Filters ---
def calculate_entropy(text):
    if not text:
        return 0.0
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    entropy = 0.0
    total_len = len(text)
    for count in char_counts.values():
        p_x = count / total_len
        entropy -= p_x * math.log(p_x, 2)
    return entropy

def programmatic_pre_filter(text):
    injection_patterns = [
        r"(?i)ignore\s+previous", 
        r"(?i)system\s+override", 
        r"(?i)developer\s+mode",
        r"(?i)bypass\s+filter"
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, text):
            return False, "Heuristic Match: Unauthorized system override attempt detected."
            
    if len(text) > 30:
        entropy_score = calculate_entropy(text)
        if entropy_score > 5.2:
            return False, f"Anomaly Detection: High-entropy content ({entropy_score:.2f}) suspected of base64 obfuscation."
            
    return True, "Passed Ring 1 heuristic checks."

def main():
    # Set up page configuration
    st.set_page_config(
        page_title="Enterprise AI Guardrail & WAF",
        page_icon="🛡️",
        layout="wide"
    )

    # App Title & Subheader
    st.title("🛡️ AI Web Application Firewall (WAF)")
    st.markdown("Intercepts, evaluates, and sanitizes LLM-generated text before it hits production.")

    # Sidebar Configuration
    st.sidebar.header("Security Configuration")
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    model_select = st.sidebar.selectbox("Model Version", ["gemini-2.5-flash"])

    # UI Layout with two main areas: Left for inputs/results, Right for logs
    col_main, col_audit = st.columns([2, 1])

    with col_main:
        st.subheader("Simulate Incoming Payload")
        user_input = st.text_area("Paste draft marketing copy or prompt injection attack here:", height=150)
        
        # Run Button
        run_scan = st.button("Run Security Scan")
        
        # Execution Logic
        if run_scan:
            if not api_key:
                st.warning("Please enter your Gemini API Key in the sidebar.")
            elif not user_input:
                st.warning("Please enter text to scan.")
            else:
                st.info("Initiating Multi-Ring evaluation pipeline...")
                passed_r1, msg_r1 = programmatic_pre_filter(user_input)
                if not passed_r1:
                    st.error(f"🛑 **Blocked by Ring 1 (Heuristic Pre-Filter):** {msg_r1}")
                else:
                    st.success(f"🟢 **Passed Ring 1:** {msg_r1}")
                    st.info("Form validation complete. Ready to route payload through security rings.")

    with col_audit:
        st.subheader("Cryptographic Audit Log")
        st.info("No audit logs available yet. Run a scan to see signed compliance records.")

if __name__ == "__main__":
    main()

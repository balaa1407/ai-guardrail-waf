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

# --- Ring 3: Cryptographic Audit ---
SECRET_AUDIT_KEY = b"enterprise_waf_secret_key_2026"

def generate_audit_signature(payload_dict):
    """Generates an HMAC-SHA256 signature for a dictionary payload."""
    payload_str = json.dumps(payload_dict, sort_keys=True)
    signature = hmac.new(SECRET_AUDIT_KEY, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

def verify_audit_signature(payload_dict, signature):
    """Verifies the HMAC-SHA256 signature."""
    expected_signature = generate_audit_signature(payload_dict)
    return hmac.compare_digest(expected_signature, signature)

def create_compliance_log(payload_text, action, reason):
    """Creates a structured, signed JSON compliance report."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload_text,
        "action": action,
        "reason": reason
    }
    signature = generate_audit_signature(log_entry)
    
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []
        
    st.session_state.audit_logs.append({
        "log": log_entry,
        "signature": signature
    })
    return log_entry, signature

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
                    create_compliance_log(user_input, "BLOCKED", f"Ring 1: {msg_r1}")
                else:
                    st.success(f"🟢 **Passed Ring 1:** {msg_r1}")
                    st.info("Form validation complete. Ready to route payload through security rings.")
                    create_compliance_log(user_input, "PASSED_R1", "Passed heuristic checks.")

    with col_audit:
        st.subheader("Cryptographic Audit Log")
        if "audit_logs" not in st.session_state or not st.session_state.audit_logs:
            st.info("No audit logs available yet. Run a scan to see signed compliance records.")
        else:
            for record in reversed(st.session_state.audit_logs):
                log = record["log"]
                sig = record["signature"]
                
                is_valid = verify_audit_signature(log, sig)
                
                with st.expander(f"{log['action']} - {log['timestamp'][:19]}"):
                    if is_valid:
                        st.success(f"Verified Signature: `{sig[:16]}...`")
                    else:
                        st.error("Signature Verification Failed! Log tampered.")
                    st.json(log)

if __name__ == "__main__":
    main()

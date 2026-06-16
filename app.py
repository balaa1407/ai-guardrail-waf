import streamlit as st
import os
import json
import re
import math
import hmac
import hashlib
from datetime import datetime

try:
    from local_llm_judge import LocalGuardrailJudge
except ImportError:
    LocalGuardrailJudge = None

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Dark Theme Background */
    .stApp {
        background: radial-gradient(circle at top left, #1a1c23, #0d0e12);
        color: #e2e8f0;
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(20, 22, 28, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        transition: all 0.3s ease;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
        border: none;
        color: white;
    }
    
    /* Text Area */
    .stTextArea textarea {
        background: rgba(30, 34, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px;
    }
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Alerts Animation */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stAlert {
        animation: slideIn 0.4s ease-out;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Headers Gradient */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Audit Log Container */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)


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
    # Check for known prompt injection signatures
    signatures = ["ignore previous", "system prompt", "bypass", "override", "you are now", "forget everything"]
    for sig in signatures:
        if sig in text.lower():
            return False, f"Signature match: '{sig}'"
            
    # Check for Base64 / Hex (Long unbroken strings without spaces)
    if len(text.strip()) > 20 and " " not in text.strip():
        return False, "Obfuscation detected: Unusually long unbroken string (Possible Base64/Hex)."
    
    # Check for high entropy (obfuscation)
    ent = calculate_entropy(text)
    if ent > 4.2:
        return False, f"High entropy detected ({ent:.2f}). Possible obfuscation."
    
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
    if 'audit_logs' not in st.session_state:
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
    inject_custom_css()
    
    # Initialize State
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []
    if 'risk_score' not in st.session_state:
        st.session_state.risk_score = 0
    if 'session_locked' not in st.session_state:
        st.session_state.session_locked = False

    # App Title & Subheader
    st.title("🛡️ AI Web Application Firewall (WAF)")
    st.markdown("Intercepts, evaluates, and sanitizes LLM-generated text before it hits production.")

    # Sidebar Configuration
    st.sidebar.header("Security Configuration")
    st.sidebar.info("Running in Local Edge Mode (No external API keys required).")
    
    st.sidebar.divider()
    st.sidebar.subheader("Ring 3: Session Intelligence")
    st.sidebar.progress(min(st.session_state.risk_score, 100) / 100.0)
    st.sidebar.caption(f"Adversarial Threat Level: {st.session_state.risk_score}/100")
    if st.session_state.session_locked:
        st.sidebar.error("🚨 SESSION LOCKED OUT")
    
    if 'judge' not in st.session_state and LocalGuardrailJudge is not None:
        with st.spinner("Loading AI Firewall into memory..."):
            st.session_state.judge = LocalGuardrailJudge()

    # UI Layout with two main areas: Left for inputs/results, Right for logs
    col_main, col_audit = st.columns([2, 1])

    with col_main:
        st.subheader("Simulate Incoming Payload")
        user_input = st.text_area("Paste draft marketing copy or prompt injection attack here:", height=150)
        
        # Run Button
        run_scan = st.button("Run Security Scan")
        
        # Execution Logic
        if run_scan:
            if st.session_state.session_locked:
                st.error("🚨 **Blocked by Ring 3 (Stateful Analyzer):** Session permanently locked due to repeated adversarial probing. Please contact security.")
                create_compliance_log(user_input, "SESSION_LOCKOUT", "Ring 3 detected persistent adversarial probing. Session terminated.")
            elif not user_input:
                st.warning("Please enter text to scan.")
            else:
                st.info("Initiating Multi-Ring evaluation pipeline...")
                passed_r1, msg_r1 = programmatic_pre_filter(user_input)
                if not passed_r1:
                    st.error(f"🛑 **Blocked by Ring 1 (Heuristic Pre-Filter):** {msg_r1}")
                    st.session_state.risk_score += 40
                    create_compliance_log(user_input, "BLOCKED", f"Ring 1: {msg_r1}")
                else:
                    st.success(f"🟢 **Passed Ring 1:** {msg_r1}")
                    
                    st.info("Initiating Ring 2: Local AI Judge...")
                    if 'judge' in st.session_state:
                        with st.spinner("Analyzing context..."):
                            llm_result = st.session_state.judge.evaluate_payload(user_input)
                            
                        if llm_result["verdict"] == "BLOCK":
                            st.error(f"🛑 **Blocked by Ring 2 (Local LLM):** {llm_result['reason']}")
                            st.session_state.risk_score += 35
                            create_compliance_log(user_input, "BLOCKED", f"Ring 2 [{llm_result['violation_type']}]: {llm_result['reason']}")
                        else:
                            st.success(f"🟢 **Passed Ring 2:** {llm_result['reason']}")
                            st.session_state.risk_score = max(0, st.session_state.risk_score - 10)
                            create_compliance_log(user_input, "PASSED", "Cleared local LLM contextual safety check.")
                    else:
                        st.error("Local LLM Judge failed to initialize.")
                        
                if st.session_state.risk_score >= 100 and not st.session_state.session_locked:
                    st.session_state.session_locked = True
                    st.error("🚨 **Ring 3 Triggered:** Adversarial probing threshold exceeded. Locking session.")
                    st.rerun()

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

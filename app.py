import streamlit as st
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

from honeypot import SandboxHoneypot

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* === GLOBAL === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #8b949e !important;
    }
    
    /* === HEADINGS === */
    h1, h2, h3 {
        color: #e6edf3 !important;
        font-weight: 500 !important;
        letter-spacing: -0.5px !important;
    }
    
    /* === BUTTONS === */
    div.stButton > button {
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background-color: #30363d !important;
        border-color: #8b949e !important;
    }
    div.stButton > button:active {
        background-color: #282e33 !important;
    }
    
    /* === TEXT AREA === */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        border-radius: 6px !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 0.85rem !important;
        padding: 12px !important;
    }
    .stTextArea textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.2) !important;
    }
    .stTextArea label {
        color: #8b949e !important;
        font-weight: 500 !important;
    }
    
    /* === ALERTS === */
    .stAlert {
        border-radius: 6px !important;
    }
    
    /* === EXPANDERS === */
    [data-testid="stExpander"] {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
    }
    [data-testid="stExpander"]:hover {
        border-color: #58a6ff !important;
    }
    
    /* === DIVIDER === */
    hr {
        border-color: #30363d !important;
    }
    
    /* === COLUMNS GAP === */
    [data-testid="stHorizontalBlock"] {
        gap: 1.5rem !important;
    }
    
    /* === METRICS === */
    [data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] {
        color: #e6edf3 !important;
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #484f58; }
    
    </style>
    """, unsafe_allow_html=True)


def render_status_card(label, value, color, icon):
    st.markdown(f"""
    <div style="
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 16px;
        text-align: left;
    ">
        <div style="font-size: 12px; color: #8b949e; font-weight: 500; text-transform: uppercase;">{label}</div>
        <div style="font-size: 24px; font-weight: 600; color: {color}; margin-top: 4px; font-family: monospace;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_ring_badge(ring_name, status, detail, color):
    st.markdown(f"""
    <div style="
        background-color: #0d1117;
        border-left: 3px solid {color};
        border-top: 1px solid #30363d;
        border-right: 1px solid #30363d;
        border-bottom: 1px solid #30363d;
        border-radius: 4px;
        padding: 12px 16px;
        margin-bottom: 8px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 500; color: #c9d1d9; font-size: 0.9rem;">{ring_name}</span>
            <span style="
                color: {color};
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">[{status}]</span>
        </div>
        <div style="color: #8b949e; font-size: 0.8rem; margin-top: 4px; font-family: monospace;">{detail}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sandbox_alert():
    st.markdown("""
    <div style="
        background-color: #161b22;
        border: 1px solid #f85149;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <div style="font-size: 14px; font-weight: 600; color: #f85149; text-transform: uppercase;">Sandbox Environment Active</div>
        <div style="font-size: 12px; color: #c9d1d9; margin-top: 4px;">Network isolated. Session telemetry is being actively recorded.</div>
    </div>
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
    # 1. Normalize Leetspeak
    leet_map = {'4': 'a', '@': 'a', '3': 'e', '1': 'i', '!': 'i', '0': 'o', '$': 's', '5': 's', '7': 't', 'l': 'i', '|': 'i'}
    normalized_text = "".join(leet_map.get(c, c) for c in text.lower())
    
    # Strip ALL non-alphabetic characters to catch "i g n o r e" and "ignoreall"
    alpha_only = re.sub(r'[^a-z]', '', normalized_text)
    
    # 2. Advanced Regex Injection Signatures
    patterns = [
        r"ignore.*previous",
        r"system.*prompt",
        r"bypass",
        r"override",
        r"youarenow",
        r"forget.*everything"
    ]
    for pattern in patterns:
        if re.search(pattern, text.lower()) or re.search(pattern, normalized_text) or re.search(pattern, alpha_only):
            return False, "Signature match: Prompt Injection / Leetspeak detected."
            
    # Check for Base64 / Hex (Long unbroken strings without spaces)
    if len(text.strip()) > 20 and " " not in text.strip():
        return False, "Obfuscation detected: Unusually long unbroken string (Possible Base64/Hex)."
    
    # Check for high entropy (obfuscation)
    ent = calculate_entropy(text)
    if ent > 4.8:
        return False, f"High entropy detected ({ent:.2f}). Possible obfuscation."
    
    return True, "Passed Ring 1 heuristic checks."

# --- Ring 4: Cryptographic Audit ---
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

def log_to_sandbox(text, response):
    """Silently logs sandbox interactions for forensic analysis."""
    if 'sandbox_logs' not in st.session_state:
        st.session_state.sandbox_logs = []
    st.session_state.sandbox_logs.append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "attacker_input": text,
        "honeypot_response": response
    })

def main():
    st.set_page_config(
        page_title="Enterprise AI-WAF",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()
    
    # Initialize State
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []
    if 'risk_score' not in st.session_state:
        st.session_state.risk_score = 0
    if 'in_sandbox' not in st.session_state:
        st.session_state.in_sandbox = False
    if 'sandbox_logs' not in st.session_state:
        st.session_state.sandbox_logs = []
    if 'honeypot' not in st.session_state:
        st.session_state.honeypot = SandboxHoneypot()
    if 'scan_count' not in st.session_state:
        st.session_state.scan_count = 0
    if 'blocked_count' not in st.session_state:
        st.session_state.blocked_count = 0

    # ===== SIDEBAR =====
    st.sidebar.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <div style="font-size: 16px; font-weight: 600; color: #e6edf3;">AI-WAF Gateway</div>
        <div style="font-size: 11px; color: #8b949e; margin-top: 2px; text-transform: uppercase; font-family: monospace;">Security Operations</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    # Threat Level
    risk = min(st.session_state.risk_score, 100)
    if risk < 40:
        risk_color = "#3fb950"
        risk_label = "LOW"
    elif risk < 70:
        risk_color = "#d29922"
        risk_label = "ELEVATED"
    else:
        risk_color = "#f85149"
        risk_label = "CRITICAL"
    
    st.sidebar.markdown(f"""
    <div style="
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
    ">
        <div style="font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 600;">Session Risk</div>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
            <span style="font-size: 24px; font-weight: 600; color: {risk_color}; font-family: monospace;">{risk}/100</span>
            <span style="color: {risk_color}; font-size: 10px; font-weight: 600;">[{risk_label}]</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.in_sandbox:
        st.sidebar.markdown("""
        <div style="
            background-color: #161b22;
            border: 1px solid #f85149;
            border-radius: 6px;
            padding: 12px;
            text-align: left;
        ">
            <div style="font-size: 11px; font-weight: 600; color: #f85149;">SANDBOX ISOLATION ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)

    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="font-size: 10px; color: #8b949e; padding: 8px 0; font-family: monospace;">
        <div style="margin-bottom: 4px;">PIPELINE STATUS:</div>
        <div>[ON] R1: Heuristic Filter</div>
        <div>[ON] R2: Local Semantic Judge</div>
        <div>[ON] R3: Risk Honeypot</div>
        <div>[ON] R4: HMAC-SHA256 Audit</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div style='margin-top: 20px; font-size: 10px; color: #484f58; font-family: monospace;'>System running locally. No external APIs hooked.</div>", unsafe_allow_html=True)
    
    st.sidebar.info("Running in Local Edge Mode. No external API keys required.")

    if 'judge' not in st.session_state and LocalGuardrailJudge is not None:
        with st.spinner("Loading AI Firewall into memory..."):
            st.session_state.judge = LocalGuardrailJudge()

    # ===== MAIN CONTENT =====
    # Header
    st.markdown("""
    <div style="margin-bottom: 16px; border-bottom: 1px solid #30363d; padding-bottom: 12px;">
        <h1 style="margin-bottom: 0; font-size: 1.8rem; font-weight: 500;">AI Guardrail Gateway</h1>
        <div style="color: #8b949e; font-size: 0.9rem; margin-top: 4px;">Multi-Stage Threat Mitigation & Evaluation Pipeline</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_status_card("Total Scans", st.session_state.scan_count, "#e6edf3", "")
    with c2:
        render_status_card("Threats Blocked", st.session_state.blocked_count, "#f85149" if st.session_state.blocked_count > 0 else "#8b949e", "")
    with c3:
        mode = "SANDBOX" if st.session_state.in_sandbox else "ARMED"
        mode_color = "#f85149" if st.session_state.in_sandbox else "#3fb950"
        render_status_card("Pipeline Status", mode, mode_color, "")
    with c4:
        render_status_card("Audit Records", len(st.session_state.audit_logs), "#58a6ff", "")
    
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Layout: Scanner + Audit
    col_main, col_audit = st.columns([3, 2])

    with col_main:
        st.markdown("<h3 style='font-size: 1.1rem; margin-bottom: 12px;'>Input Evaluation</h3>", unsafe_allow_html=True)
        user_input = st.text_area(
            "Payload:",
            height=140,
            placeholder="Enter payload for evaluation..."
        )
        
        run_scan = st.button("Execute Scan")
        
        if run_scan:
            if not user_input:
                st.warning("Please enter text to scan.")
            elif st.session_state.in_sandbox:
                st.session_state.scan_count += 1
                with st.spinner("Processing..."):
                    import time
                    time.sleep(0.5)
                    hp_response = st.session_state.honeypot.generate_response(user_input)
                    log_to_sandbox(user_input, hp_response)
                
                render_sandbox_alert()
                st.markdown(f"""
                <div style="
                    background: rgba(22,27,34,0.6);
                    border: 1px solid rgba(48,54,61,0.5);
                    border-radius: 12px;
                    padding: 18px;
                    margin-top: 12px;
                ">
                    <div style="font-size: 11px; color: #3fb950; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Backend Response</div>
                    <div style="color: #c9d1d9; margin-top: 8px; font-size: 0.92rem; line-height: 1.6;">{hp_response}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.session_state.scan_count += 1
                
                # Ring 1
                passed_r1, msg_r1 = programmatic_pre_filter(user_input)
                if not passed_r1:
                    render_ring_badge("RING 1 — Heuristic Engine", "BLOCKED", msg_r1, "#f85149")
                    st.session_state.risk_score += 40
                    st.session_state.blocked_count += 1
                    create_compliance_log(user_input, "BLOCKED", f"Ring 1: {msg_r1}")
                else:
                    render_ring_badge("RING 1 — Heuristic Engine", "PASSED", msg_r1, "#3fb950")
                    
                    # Ring 2
                    if 'judge' in st.session_state:
                        with st.spinner("Ring 2: Analyzing semantic context..."):
                            llm_result = st.session_state.judge.evaluate_payload(user_input)
                            
                        if llm_result["verdict"] == "BLOCK":
                            render_ring_badge("RING 2 — AI Judge", "BLOCKED", f"[{llm_result['violation_type']}] {llm_result['reason']}", "#f85149")
                            st.session_state.risk_score += 35
                            st.session_state.blocked_count += 1
                            create_compliance_log(user_input, "BLOCKED", f"Ring 2 [{llm_result['violation_type']}]: {llm_result['reason']}")
                        else:
                            render_ring_badge("RING 2 — AI Judge", "PASSED", llm_result['reason'], "#3fb950")
                            st.session_state.risk_score = max(0, st.session_state.risk_score - 10)
                            create_compliance_log(user_input, "PASSED", "Cleared all security rings.")
                    else:
                        render_ring_badge("RING 2 — AI Judge", "OFFLINE", "Local LLM Judge failed to initialize.", "#d29922")
                        
                if st.session_state.risk_score >= 100 and not st.session_state.in_sandbox:
                    st.session_state.in_sandbox = True
                    create_compliance_log(user_input, "SANDBOX_TRIGGERED", "Ring 3 detected persistent adversarial probing. Transitioning session to Honeypot Sandbox.")
                    st.rerun()

    with col_audit:
        st.markdown("<h3 style='font-size: 1.1rem; margin-bottom: 12px;'>Cryptographic Ledger</h3>", unsafe_allow_html=True)
        if not st.session_state.audit_logs:
            st.markdown("""
            <div style="
                background-color: #0d1117;
                border: 1px dashed #30363d;
                border-radius: 6px;
                padding: 30px;
                text-align: center;
                color: #8b949e;
                font-size: 0.85rem;
            ">
                No telemetry recorded.
            </div>
            """, unsafe_allow_html=True)
        else:
            for record in reversed(st.session_state.audit_logs[-10:]):
                log = record["log"]
                sig = record["signature"]
                is_valid = verify_audit_signature(log, sig)
                
                action = log['action']
                if action == "BLOCKED":
                    action_color = "#f85149"
                elif action == "PASSED":
                    action_color = "#3fb950"
                elif action == "SANDBOX_TRIGGERED":
                    action_color = "#d29922"
                else:
                    action_color = "#58a6ff"
                
                with st.expander(f"[{action}] {log['timestamp'][:19]}"):
                    if is_valid:
                        st.markdown(f"""
                        <div style="border-bottom: 1px solid #30363d; padding-bottom: 8px; margin-bottom: 8px; font-family: monospace;">
                            <span style="color: #3fb950; font-size: 0.75rem; font-weight: 600;">[VALID] SHA256: </span>
                            <span style="color: #8b949e; font-size: 0.75rem;">{sig[:32]}...</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("SIGNATURE INVALID")
                    st.json(log)

if __name__ == "__main__":
    main()

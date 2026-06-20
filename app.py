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

from honeypot import SandboxHoneypot

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* === GLOBAL === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0b0f 0%, #111318 40%, #0d1117 100%);
        color: #c9d1d9;
    }
    
    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(13,17,23,0.95) 0%, rgba(22,27,34,0.95) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(48,54,61,0.6) !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #8b949e !important;
    }
    
    /* === HEADINGS === */
    h1 {
        background: linear-gradient(135deg, #58a6ff 0%, #bc8cff 50%, #f778ba 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
    }
    h2, h3 {
        background: linear-gradient(90deg, #79c0ff, #d2a8ff) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 700 !important;
    }
    
    /* === GLOW BUTTON === */
    div.stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(46,160,67,0.4) !important;
        border-radius: 10px !important;
        padding: 0.65rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 0 20px rgba(46,160,67,0.15), 0 4px 12px rgba(0,0,0,0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 30px rgba(46,160,67,0.3), 0 8px 24px rgba(0,0,0,0.4) !important;
        background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(46,160,67,0.6) !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* === TEXT AREA === */
    .stTextArea textarea {
        background: rgba(13,17,23,0.8) !important;
        border: 1px solid rgba(48,54,61,0.8) !important;
        color: #c9d1d9 !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
        padding: 14px !important;
        transition: all 0.3s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 3px rgba(88,166,255,0.15), 0 0 20px rgba(88,166,255,0.1) !important;
    }
    .stTextArea label {
        color: #8b949e !important;
        font-weight: 500 !important;
    }
    
    /* === ALERTS === */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stAlert {
        animation: slideUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(8px) !important;
    }
    
    /* === EXPANDERS === */
    [data-testid="stExpander"] {
        background: rgba(22,27,34,0.6) !important;
        border: 1px solid rgba(48,54,61,0.5) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stExpander"]:hover {
        border-color: rgba(88,166,255,0.3) !important;
    }
    
    /* === PROGRESS BAR === */
    .stProgress > div > div {
        border-radius: 6px !important;
    }
    
    /* === DIVIDER === */
    hr {
        border-color: rgba(48,54,61,0.5) !important;
    }
    
    /* === COLUMNS GAP === */
    [data-testid="stHorizontalBlock"] {
        gap: 1.5rem !important;
    }

    /* === METRICS === */
    [data-testid="stMetric"] {
        background: rgba(22,27,34,0.5) !important;
        border: 1px solid rgba(48,54,61,0.4) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(88,166,255,0.2); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(88,166,255,0.4); }
    
    </style>
    """, unsafe_allow_html=True)


def render_status_card(label, value, color, icon):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(22,27,34,0.7), rgba(30,36,44,0.5));
        border: 1px solid {color}33;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        box-shadow: 0 0 25px {color}10, 0 4px 16px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    ">
        <div style="font-size: 28px; margin-bottom: 6px;">{icon}</div>
        <div style="font-size: 13px; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
        <div style="font-size: 26px; font-weight: 800; color: {color}; margin-top: 4px;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_ring_badge(ring_name, status, detail, color):
    bg = f"{color}12"
    border = f"{color}40"
    st.markdown(f"""
    <div style="
        background: {bg};
        border-left: 4px solid {color};
        border-radius: 0 10px 10px 0;
        padding: 14px 18px;
        margin-bottom: 10px;
        backdrop-filter: blur(8px);
        animation: slideUp 0.4s ease-out;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: {color}; font-size: 0.95rem;">{ring_name}</span>
            <span style="
                background: {color}22;
                color: {color};
                padding: 3px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                border: 1px solid {border};
            ">{status}</span>
        </div>
        <div style="color: #8b949e; font-size: 0.85rem; margin-top: 6px;">{detail}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sandbox_alert():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(248,81,73,0.08), rgba(210,50,45,0.04));
        border: 1px solid rgba(248,81,73,0.3);
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        animation: pulse 2s infinite;
        box-shadow: 0 0 40px rgba(248,81,73,0.08);
    ">
        <div style="font-size: 36px; margin-bottom: 8px;">🕳️</div>
        <div style="font-size: 18px; font-weight: 800; color: #f85149; letter-spacing: 1px;">SCHR&Ouml;DINGER'S SANDBOX</div>
        <div style="font-size: 13px; color: #f8514990; margin-top: 6px; font-weight: 500;">Target is trapped in honeypot simulation</div>
        <div style="font-size: 11px; color: #484f58; margin-top: 10px;">All inputs are being silently recorded for forensic analysis</div>
    </div>
    <style>
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(248,81,73,0.05); }
        50% { box-shadow: 0 0 40px rgba(248,81,73,0.15); }
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
    if ent > 4.2:
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
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <div style="font-size: 40px;">🛡️</div>
        <div style="font-size: 18px; font-weight: 800; background: linear-gradient(135deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 4px;">AI-WAF Console</div>
        <div style="font-size: 11px; color: #484f58; margin-top: 4px; letter-spacing: 1px;">ENTERPRISE SECURITY</div>
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
        risk_label = "MEDIUM"
    elif risk < 100:
        risk_color = "#f85149"
        risk_label = "HIGH"
    else:
        risk_color = "#f85149"
        risk_label = "CRITICAL"
    
    st.sidebar.markdown(f"""
    <div style="
        background: rgba(22,27,34,0.6);
        border: 1px solid rgba(48,54,61,0.5);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    ">
        <div style="font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">Threat Level</div>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 6px;">
            <span style="font-size: 32px; font-weight: 800; color: {risk_color};">{risk}</span>
            <span style="
                background: {risk_color}18;
                color: {risk_color};
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 700;
                border: 1px solid {risk_color}40;
                letter-spacing: 0.5px;
            ">{risk_label}</span>
        </div>
        <div style="
            background: rgba(48,54,61,0.5);
            border-radius: 4px;
            height: 6px;
            margin-top: 10px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {risk_color}, {risk_color}aa);
                width: {risk}%;
                height: 100%;
                border-radius: 4px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.in_sandbox:
        st.sidebar.markdown("""
        <div style="
            background: rgba(248,81,73,0.08);
            border: 1px solid rgba(248,81,73,0.25);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
            animation: pulse 2s infinite;
        ">
            <div style="font-size: 13px; font-weight: 700; color: #f85149;">🕳️ SANDBOX ACTIVE</div>
            <div style="font-size: 10px; color: #f8514980; margin-top: 3px;">Honeypot engaged</div>
        </div>
        <style>@keyframes pulse { 0%,100%{opacity:0.8} 50%{opacity:1} }</style>
        """, unsafe_allow_html=True)

    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="font-size: 10px; color: #30363d; text-align: center; padding: 8px 0;">
        <div style="letter-spacing: 1px;">RINGS ACTIVE</div>
        <div style="margin-top: 6px; display: flex; justify-content: center; gap: 8px;">
            <span style="background: #238636; padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 9px; font-weight: 600;">R1</span>
            <span style="background: #1f6feb; padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 9px; font-weight: 600;">R2</span>
            <span style="background: #8b5cf6; padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 9px; font-weight: 600;">R3</span>
            <span style="background: #d29922; padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 9px; font-weight: 600;">R4</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.info("Running in Local Edge Mode. No external API keys required.")

    if 'judge' not in st.session_state and LocalGuardrailJudge is not None:
        with st.spinner("Loading AI Firewall into memory..."):
            st.session_state.judge = LocalGuardrailJudge()

    # ===== MAIN CONTENT =====
    # Header
    st.markdown("""
    <div style="margin-bottom: 8px;">
        <h1 style="margin-bottom: 0; font-size: 2.2rem;">AI Web Application Firewall</h1>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Multi-Ring Defense-in-Depth Security Pipeline  |  Intercept  ·  Evaluate  ·  Sanitize")
    
    # Status Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_status_card("Total Scans", st.session_state.scan_count, "#58a6ff", "📊")
    with c2:
        render_status_card("Threats Blocked", st.session_state.blocked_count, "#f85149", "🛑")
    with c3:
        mode = "SANDBOX" if st.session_state.in_sandbox else "ARMED"
        mode_color = "#f85149" if st.session_state.in_sandbox else "#3fb950"
        render_status_card("WAF Status", mode, mode_color, "🔒" if not st.session_state.in_sandbox else "🕳️")
    with c4:
        render_status_card("Audit Logs", len(st.session_state.audit_logs), "#d2a8ff", "📋")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Layout: Scanner + Audit
    col_main, col_audit = st.columns([3, 2])

    with col_main:
        st.markdown("### 🔍 Payload Scanner")
        user_input = st.text_area(
            "Enter text to scan through the security pipeline:",
            height=140,
            placeholder="Paste a prompt injection, encoded payload, or marketing copy here..."
        )
        
        run_scan = st.button("⚡ Run Security Scan")
        
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
        st.markdown("### 📋 Cryptographic Audit Log")
        if not st.session_state.audit_logs:
            st.markdown("""
            <div style="
                background: rgba(22,27,34,0.4);
                border: 1px dashed rgba(48,54,61,0.6);
                border-radius: 12px;
                padding: 40px 20px;
                text-align: center;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">🔐</div>
                <div style="color: #484f58; font-size: 0.9rem;">No audit logs yet</div>
                <div style="color: #30363d; font-size: 0.78rem; margin-top: 4px;">Run a scan to generate signed compliance records</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for record in reversed(st.session_state.audit_logs[-10:]):
                log = record["log"]
                sig = record["signature"]
                is_valid = verify_audit_signature(log, sig)
                
                action = log['action']
                if action == "BLOCKED":
                    badge_color = "#f85149"
                    badge_icon = "🛑"
                elif action == "PASSED":
                    badge_color = "#3fb950"
                    badge_icon = "✅"
                elif action == "SANDBOX_TRIGGERED":
                    badge_color = "#d29922"
                    badge_icon = "🕳️"
                else:
                    badge_color = "#8b949e"
                    badge_icon = "📝"
                
                with st.expander(f"{badge_icon} {action} — {log['timestamp'][:19]}"):
                    if is_valid:
                        st.markdown(f"""
                        <div style="background: rgba(46,160,67,0.08); border: 1px solid rgba(46,160,67,0.2); border-radius: 8px; padding: 8px 12px; margin-bottom: 8px;">
                            <span style="color: #3fb950; font-size: 0.8rem; font-weight: 600;">✓ SIGNATURE VERIFIED</span>
                            <span style="color: #484f58; font-size: 0.72rem; margin-left: 8px; font-family: monospace;">{sig[:24]}...</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("⚠️ SIGNATURE VERIFICATION FAILED — Log may be tampered!")
                    st.json(log)

if __name__ == "__main__":
    main()

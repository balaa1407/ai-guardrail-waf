# Enterprise AI-WAF

An advanced, edge-deployed Web Application Firewall (WAF) designed specifically to protect Large Language Models (LLMs) from prompt injections, jailbreaks, and policy violations. 

Unlike traditional cloud-based moderation APIs, **Enterprise AI-WAF** runs a lightweight LLM locally on the edge. This ensures true **Zero-Trust Data Residency**—proprietary enterprise data never leaves your network.

## 🛡️ 4-Ring Defense-in-Depth Architecture

This WAF utilizes a tiered defense system to ensure maximum security without sacrificing latency.

### Ring 1: Deterministic Heuristic Engine
The first line of defense. Ring 1 uses highly optimized regular expressions and Shannon entropy calculations to instantly drop known attack signatures (e.g., Leetspeak obfuscation, SQL injection syntax, base64 encoding). This prevents wasting GPU compute on obvious attacks.

### Ring 2: Semantic AI Judge
If an input passes Ring 1, it is evaluated by our local AI Judge (powered by a locally running Gemma-2B instance). The AI Judge analyzes the semantic *intent* of the payload to catch zero-day jailbreaks, prohibited medical claims, and attempts to solicit restricted technical knowledge.

### Ring 3: Active Defense Honeypot
Traditional WAFs simply block and drop connections. We use Active Defense. If a user accumulates a critical Risk Score (e.g., repeatedly trying to breach the system), Ring 3 seamlessly shunts their session into an isolated **Honeypot Sandbox**. The attacker is fed fabricated canary data while the system records their methodologies.

### Ring 4: Cryptographic Auditing Ledger
To ensure non-repudiation and compliance, every single action (Pass, Block, Sandbox Trigger) is logged to the Security Operations Center (SOC) and cryptographically signed using an HMAC-SHA256 signature at the exact moment of execution.

## 📊 Bespoke SOC Telemetry Dashboard

The included SOC Admin Dashboard provides a unified telemetry feed of all network actions.
- **Real-Time Action Feed**: Visually triaged feed of all Passes, Blocks, and Sandbox triggers.
- **Automated Incident Response**: Leverage the local AI Judge to generate automated threat vector reports based on captured payload data.
- **Dynamic IP Traceback**: Automatically trace and geo-locate an attacker's public IP address in real-time.

## 🚀 Getting Started

1. Clone the repository.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python -m streamlit run app.py
   ```
4. Access the Main Portal at `http://localhost:8501` and the SOC Dashboard via the sidebar.

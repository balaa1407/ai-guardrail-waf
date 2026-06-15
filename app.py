import streamlit as st
import os
import json

st.set_page_config(
    page_title="Enterprise AI Guardrail & WAF",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI Web Application Firewall (WAF)")
st.markdown("Intercepts, evaluates, and sanitizes LLM-generated text before it hits production.")

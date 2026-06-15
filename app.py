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

st.sidebar.header("Security Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model_select = st.sidebar.selectbox("Model Version", ["gemini-2.5-flash"])

col_main, col_audit = st.columns([2, 1])

with col_main:
    st.subheader("Simulate Incoming Payload")
    user_input = st.text_area("Paste draft marketing copy or prompt injection attack here:", height=150)

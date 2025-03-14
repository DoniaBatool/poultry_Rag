import streamlit as st
from utils import analyze_lab_report, process_uploaded_file

# Page Title
st.title("🧪 Laboratory Report Analysis")

# Upload File (PDF, CSV, TXT, JPG, PNG)
st.subheader("📤 Upload Veterinary Lab Report")
uploaded_file = st.file_uploader("Upload a lab report", type=["pdf", "csv", "txt", "jpg", "png"])
uploaded_text = process_uploaded_file(uploaded_file) if uploaded_file else ""

if uploaded_text:
    st.success("✅ File processed successfully! AI is analyzing the report...")

    # AI Analysis using Gemini 1.5 Flash
    analysis_result = analyze_lab_report(uploaded_text)

    # Display the AI Analysis
    st.subheader("📑 AI Report Analysis")
    st.write(analysis_result)

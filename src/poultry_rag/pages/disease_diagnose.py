import streamlit as st
from PIL import Image
from utils import diagnose_poultry_disease

# Disease Diagnosis Page
st.title("🐔 Poultry Disease Diagnosis")
st.subheader("Upload an image to detect poultry diseases")

diagnosis_image = st.file_uploader("Upload a chicken image for diagnosis", type=["jpg", "png", "jpeg"])

if diagnosis_image:
    img = Image.open(diagnosis_image)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    with st.spinner("Analyzing the image..."):
        diagnosis = diagnose_poultry_disease(img)
    
    st.subheader("🩺 Diagnosis Result")
    st.write(diagnosis)

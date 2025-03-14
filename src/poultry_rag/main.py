from io import BytesIO
import os
import streamlit as st
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAI
from poultry_rag.utils import get_weather, get_youtube_videos, web_search
from poultry_rag.vectorstore import load_documents

load_dotenv()

# Pehle .env se API key lene ki koshish karein
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Agar .env me key nahi mili, toh Streamlit secrets use karein (Cloud Deployment ke liye)
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]


# Streamlit UI
st.title("🐔 EGGSPERT AI ASSISTANT")
st.subheader("Your Smart Guide for Poultry Farming, Disease Management, and Egg Production Optimization")

# Fetch Weather Data
city = st.text_input("Enter your city for weather updates:", "Karachi")

temp, humidity, wind_speed, weather_desc, recommendations = get_weather(city)

if temp is not None:
    st.write(f"🌡️ **Current Temperature in {city}:** {temp}°C")
    st.write(f"💧 **Humidity:** {humidity}%")
    st.write(f"💨 **Wind Speed:** {wind_speed} m/s")
    st.write(f"⛅ **Weather Condition:** {weather_desc.capitalize()}")

    for rec in recommendations:
        st.warning(rec)
else:
    st.error("⚠️ Unable to fetch weather data. Please check your internet or API key.")

# Sidebar Navigation
with st.sidebar:
    
    st.header("🐔 Quick Access")

    with st.expander("🧪 Laboratory"):
        st.page_link("pages/lab_analysis.py", label="Lab Report Analysis")

    with st.expander("📊 Financial Tools"):
        st.page_link("pages/profit_calculator.py", label="Profit Calculator")

    with st.expander("🩺 Disease & Treatment"):
        st.page_link("pages/disease_diagnose.py", label="Disease Diagnosis")

    with st.expander("🥚 Market Updates"):
        st.page_link("pages/egg_prices.py", label="Latest Egg Rates")
# Load vectorstore
vectorstore = load_documents()

# User Query Section
prompt = st.chat_input("Ask your poultry-related question...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if "poultry" not in prompt.lower():
        response = "⚠️ This bot only answers poultry-related questions."
    else:
        try:
            response = "### 🐔 Knowledge Base Response\n"
            seen_responses = set()

            if vectorstore:
                retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
                chain = RetrievalQA.from_chain_type(
                    llm=GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY),
                    retriever=retriever,
                    return_source_documents=True
                )

                result = chain.invoke({"query": prompt})
                knowledge_response = ""

                for doc in result["source_documents"]:
                    content = doc.page_content.strip()
                    source_pdf = doc.metadata.get("source", "Unknown PDF")

                    if content in seen_responses:
                        continue
                    seen_responses.add(content)

                    # ✅ Extracted Text
                    knowledge_response += f"\n\n📖 **Text from {source_pdf}:**\n{content}\n"

                    # ✅ Extract Tables
                    if "tables" in doc.metadata and doc.metadata["tables"]:
                        for j, table in enumerate(doc.metadata["tables"]):
                            df = pd.DataFrame(table)  # Convert dictionary back to DataFrame
                            knowledge_response += f"\n\n📊 **Table {j+1} from {source_pdf}:**\n"
                            knowledge_response += df.to_markdown()

                    # ✅ Extract Images
                    if "images" in doc.metadata:
                        for img_index, img_bytes in enumerate(doc.metadata["images"]):
                            img_pil = Image.open(BytesIO(img_bytes))
                            st.subheader(f"🖼️ Image {img_index+1} from {source_pdf}")
                            st.image(img_pil, use_column_width=True)

                response += knowledge_response

            # 🔍 Web Search Results
            response += "\n\n## 🔍 Web Search Results\n"

            search_results = web_search(prompt)

            if search_results:
                response += "\n".join(
                    [f"### [{result['title']}]({result['url']})\n📝 {result.get('snippet', 'No description available.')}\n" for result in search_results]
                )
            else:
                response += "⚠️ No relevant results found."

            # 🎥 Related YouTube Videos
            response += "\n\n## 🎥 Related YouTube Videos\n"
            
            videos = get_youtube_videos(prompt)
            
            if videos and videos.strip():
                response += videos
            else:
                response += "⚠️ No relevant videos found."

        except Exception as e:
            response = f"❌ Error: {str(e)}"

    st.chat_message("assistant").markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

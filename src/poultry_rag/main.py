
import os
import streamlit as st
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from utils import get_weather
from langchain.embeddings import HuggingFaceEmbeddings
import requests
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
import google.generativeai as genai

# ✅ Load Environment Variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or st.secrets.get("YOUTUBE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") or st.secrets.get("GOOGLE_CSE_ID")
GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API") or st.secrets.get("GOOGLE_SEARCH_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

# ✅ Streamlit UI
st.title("🐔 EGGSPERT AI ASSISTANT")
st.subheader("Your Smart Guide for Poultry Farming, Disease Management, and Egg Production Optimization")

# ✅ Fetch Weather Data
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

# ✅ Sidebar Navigation
with st.sidebar:
    st.header("🐔 Quick Access")
    with st.expander("🧪 Laboratory"):
        st.markdown("[Lab Report Analysis](pages/lab_analysis.py)")
    with st.expander("📊 Financial Tools"):
        st.markdown("[Profit Calculator](pages/profit_calculator.py)")
    with st.expander("🩺 Disease & Treatment"):
        st.markdown("[Disease Diagnosis](pages/disease_diagnose.py)")
    with st.expander("🥚 Market Updates"):
        st.markdown("[Latest Egg Rates](pages/egg_prices.py)")

# ✅ Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []

# ✅ Initialize the Groq Chat Model
groq_chat = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama3-8b-8192"
)

# ✅ Load Vector Store (PDF Knowledge Base)
@st.cache_resource
def get_vectorstore():
    BASE_DIR = os.getcwd()  # Streamlit does not support __file__
    pdf_files = [
        os.path.join(BASE_DIR, "docs", "poultry1.pdf"),
        os.path.join(BASE_DIR, "docs", "poultry2.pdf"),
        os.path.join(BASE_DIR, "docs", "poultry3.pdf"),
    ]

    # ✅ Debug Missing PDFs
    for pdf in pdf_files:
        if not os.path.exists(pdf):
            st.error(f"File not found: {pdf}")
            raise FileNotFoundError(f"File not found: {pdf}")

    loaders = [PyPDFLoader(pdf) for pdf in pdf_files]

    index = VectorstoreIndexCreator(
        embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2'),
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    ).from_loaders(loaders)

    return index.vectorstore

# ✅ AI-Based Query Check (Relevance Detection)
def is_relevant_query_ai(query):
    prompt = f"""
    You are an AI assistant specialized in poultry farming. 
    Analyze the user query and determine if it is related to poultry farming, poultry diseases, poultry medicine, egg production, or poultry treatment.

    If the query is relevant, return only: **"YES"**  
    If the query is NOT related to poultry, return only: **"NO"**  
      
    User Query: "{query}"
    """
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([prompt]).text.strip()
    return response == "YES"

# ✅ Web Search Function
def web_search(query, num_results=5):
    if not GOOGLE_SEARCH_API or not GOOGLE_CSE_ID:
        st.error("⚠️ Google Search API Key or CSE ID is missing!")
        return []

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"q": query, "key": GOOGLE_SEARCH_API, "cx": GOOGLE_CSE_ID, "num": num_results}
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        print("🔍 Web Search Response:", data)

        return data.get("items", [])

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Web search failed: {e}")
        return []

# ✅ YouTube Search Function
def search_youtube_videos(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        print("🎥 YouTube Search Response:", data)

        return data.get("items", [])

    except Exception as e:
        st.error(f"❌ YouTube search failed: {str(e)}")
        return []

# ✅ Show previous messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# ✅ Take user input
prompt = st.chat_input("Ask me anything about Poultry Farming!")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # ✅ Step 1: Check if query is poultry-related
        if not is_relevant_query_ai(prompt):
            st.chat_message("assistant").markdown("❌ This chatbot is specialized for poultry-related topics.")
            st.stop()

        # ✅ Step 2: Load Knowledge Base
        vectorstore = get_vectorstore()
        if vectorstore is None:
            st.error("Failed to load the document")
            st.stop()

        # ✅ Step 3: Query Knowledge Base
        chain = RetrievalQA.from_chain_type(
            llm=groq_chat,
            chain_type='stuff',
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        kb_result = chain({"query": prompt, "chat_history": st.session_state.chat_history})
        kb_response = kb_result.get("result", "❌ No knowledge base results.")

        # ✅ Step 4: Fetch Web & YouTube Results
        web_response = web_search(prompt) or "❌ No web search results."
        videos_response = search_youtube_videos(prompt) or "❌ No videos found."

        # ✅ Step 5: Display Response
        final_response = f"### 📖 Knowledge Base:\n{kb_response}\n\n### 🌍 Web:\n{web_response}\n\n### 🎥 Videos:\n{videos_response}"
        st.chat_message("assistant").markdown(final_response, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": final_response})

    except Exception as e:
        st.error(f"Error: [{str(e)}]")

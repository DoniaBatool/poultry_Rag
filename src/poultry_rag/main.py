
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




load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or st.secrets.get("YOUTUBE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") or st.secrets.get("GOOGLE_CSE_ID")
GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API") or st.secrets.get("GOOGLE_SEARCH_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")


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

 #==================================================================================       
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
    model_name="llama3-8b-8192")

#file path

@st.cache_resource
def get_vectorstore():
    # Fix BASE_DIR by getting the correct parent directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

   
    # Adjust file paths (Make sure "src/poultry_rag" is not duplicated)
    pdf_files = [
        os.path.join(BASE_DIR, "docs", "poultry1.pdf"),
        os.path.join(BASE_DIR, "docs", "poultry2.pdf"),
        os.path.join(BASE_DIR, "docs", "poultry3.pdf"),
    ]

    # Debug: Print resolved paths
    for pdf in pdf_files:
        if not os.path.exists(pdf):
            st.error(f"File not found: {pdf}")
            raise FileNotFoundError(f"File not found: {pdf}")

    # Load PDFs
    loaders = [PyPDFLoader(pdf) for pdf in pdf_files]

    # Create vector store
    index = VectorstoreIndexCreator(
        embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2'),
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    ).from_loaders(loaders)

    return index.vectorstore

# ✅ Web Search Function

genai.configure(api_key=GOOGLE_API_KEY)
# Function to perform Google Search
def web_search(query, num_results=5):
    """Fetch top search results from Google Custom Search API."""
    GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

    if not GOOGLE_SEARCH_API or not GOOGLE_CSE_ID:
        print("⚠️ API Key or Search Engine ID is missing!")
        return []

    try:
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": GOOGLE_SEARCH_API,
            "cx": GOOGLE_CSE_ID,
            "num": num_results
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses

        results = response.json().get("items", [])
        search_results = []

        for item in results:
            search_results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("link", "#"),
                "snippet": item.get("snippet", "No description available.")
            })

        return search_results

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching web search results: {e}")
        return []



# ✅ YouTube Video Search
def search_youtube_videos(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "items" in data:
            videos = data["items"][:3]  # Get top 3 videos
            if not videos:
                return "No videos found."

            video_html = ""
            for vid in videos:
                video_id = vid["id"]["videoId"]
                title = vid["snippet"]["title"]
                video_html += f'🎥 **[{title}](https://www.youtube.com/watch?v={video_id})**\n\n'
            return video_html
        
        return "No video results found."
    
    except Exception as e:
        return f"❌ Error fetching videos: {str(e)}"

# ✅ Function to check if the query is related to Cupping Therapy
def is_relevant_query(query):
    relevant_keywords = ["poultry"]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in relevant_keywords)

# ✅ Show previous messages to maintain chat history
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    st.chat_message(role).markdown(msg["content"])

# ✅ Take user input
prompt = st.chat_input("Ask me anything about Poultry Farming!")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        vectorstore = get_vectorstore()
        if vectorstore is None:
            st.error("Failed to load the document")

        # ✅ Step 1: Search in Knowledge Base
        chain = RetrievalQA.from_chain_type(
            llm=groq_chat,
            chain_type='stuff',
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True  
        )    
        kb_result = chain({"query": prompt, "chat_history": st.session_state.chat_history})
        kb_response = kb_result["result"]

        # ✅ Step 2: Web Search & YouTube Search (Only for Relevant Queries)
        if is_relevant_query(prompt):
            web_response = web_search(prompt)
            videos_response = search_youtube_videos(prompt)
        else:
            web_response = "❌ This chatbot is specialized for poultry only. Please ask relevant questions."
            videos_response = "❌ No video results as this query is not related to poultry."

        # ✅ Display assistant response with all sources
        final_response = f"""
### 📖 Knowledge Base Response:
{kb_response}

---

### 🌍 Web Search Results:
{web_response}

---

### 🎥 Video Results:
{videos_response}
"""

        # ✅ Display the response
        st.chat_message("assistant").markdown(final_response, unsafe_allow_html=True)

        # ✅ Feedback Section
        feedback_option = st.radio("Was this response helpful?", ["Yes", "No"], index=None, key=f"feedback_{len(st.session_state.messages)}")
        if feedback_option:
            st.session_state.feedback.append({"query": prompt, "response": kb_response, "feedback": feedback_option})
            st.success("✅ Thank you for your feedback!")

        # ✅ Save messages in session state
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.session_state.chat_history.append((prompt, kb_response))
    
    except Exception as e:
        st.error(f"Error: [{str(e)}]")




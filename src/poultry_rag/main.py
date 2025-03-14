
import os
import streamlit as st
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from utils import get_weather
from langchain.embeddings import HuggingFaceEmbeddings
import requests
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq




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

@st.cache_resource
def get_vectorstore():
    pdf_files = [
        "./src/poultry_rag/docs/poultry1.pdf", 
        "./src/poultry_rag/docs/poultry2.pdf",
        "./src/poultry_rag/docs/poultry3.pdf",
    ]
    loaders = [PyPDFLoader(pdf) for pdf in pdf_files]
    index = VectorstoreIndexCreator(
        embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2'),
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    ).from_loaders(loaders)
    return index.vectorstore

# ✅ Web Search Function
def search_web(query):
    url = f"https://www.searchapi.io/api/v1/search?engine=duckduckgo&q={query}&api_key={GOOGLE_SEARCH_API}"
    response = requests.get(url)
    data = response.json()
    if "organic_results" in data:
        results = data["organic_results"]
        top_results = "\n\n".join([f"**🔗 [{res['title']}]({res['link']})**\n{res['snippet']}" for res in results[:3]])
        return top_results
    return "No relevant web results found."

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
            web_response = search_web(prompt)
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




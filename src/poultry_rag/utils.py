import os
import pytesseract
import requests
from dotenv import load_dotenv
import pandas as pd
from PIL import Image
import fitz  
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# Load environment variables (Only once)
load_dotenv()
# 🔹 Pehle .env se API key lene ki koshish karein
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or st.secrets.get("YOUTUBE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") or st.secrets.get("GOOGLE_CSE_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API") or st.secrets.get("GOOGLE_SEARCH_API")

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
#youtube search results

def get_youtube_videos(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}&maxResults=3"
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()
        items = data.get("items", [])

        if not items:
            return "⚠️ No relevant videos found."

        videos = []
        for item in items:
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            description = item["snippet"]["description"].split(".")[0]  # Extract first sentence
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            videos.append(f"📹 **[{title}]({video_url})**\n📝 {description}...\n")

        return "\n".join(videos)

    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching YouTube videos: {e}"
# Function to fetch weather data and give poultry recommendations
def get_weather(city="Karachi"):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        weather_desc = data["weather"][0]["description"]

        # Calculate "Real Feel" Temperature
        heat_index = temp + (0.33 * humidity) - (0.7 * wind_speed) - 4

        recommendations = []

        if temp > 35:
            recommendations.append("🔥 Extreme heat detected! Provide electrolytes & ensure shade for poultry.")
        elif temp < 15:
            recommendations.append("❄️ Cold alert! Use heaters & deep bedding to keep birds warm.")

        if wind_speed > 20:
            recommendations.append("💨 Strong winds detected! Secure poultry houses properly.")

        if "rain" in weather_desc.lower():
            recommendations.append("☔ Rain alert! Keep sheds dry and ensure proper drainage.")

        recommendations.append(f"🌡️ Real Feel Temperature: {round(heat_index, 1)}°C")

        return temp, humidity, wind_speed, weather_desc, recommendations
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None, None, None, None, ["⚠️ Unable to fetch weather data."]
    
# Function to fetch latest egg prices from eggrates.pk


def get_egg_prices():
    try:
        url = "https://eggrates.pk/"  # URL to scrape
        response = requests.get(url)
        response.raise_for_status()  # Raise error if request fails
        
        soup = BeautifulSoup(response.text, "html.parser")

        cities = ["Islamabad", "Lahore", "Karachi", "Peshawar"]
        egg_prices = []

        for city in cities:
            city_data = {"City": city}
            city_heading = soup.find("h3", string=lambda text: text and city in text)

            if city_heading:
                # Find the nearest column containing price data
                city_column = city_heading.find_parent("div", class_="wp-block-column")

                if city_column:
                    price_paragraphs = city_column.find_all("p", class_="has-text-align-center")

                    # Extract relevant price details
                    for para in price_paragraphs:
                        text = para.get_text(strip=True)

                        if "Dozan" in text or "1 Dozen" in text:
                            city_data["Price Per Dozen"] = text
                        elif "1 Egg" in text or "Egg Rate" in text:
                            city_data["Price Per Egg"] = text
                        elif "30" in text and ("Tray" in text or "Dozen" in text):
                            city_data["30 Eggs Tray Price"] = text

                    egg_prices.append(city_data)

        return egg_prices if egg_prices else ["⚠️ No relevant results found."]
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching egg prices: {e}")
        return ["⚠️ Unable to fetch egg prices."]



# Function for multimodal file analysis
def process_uploaded_file(uploaded_file):
    file_extension = uploaded_file.name.split(".")[-1]
    extracted_text = ""

    if file_extension == "pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        extracted_text = "\n".join([page.get_text("text") for page in doc])

    elif file_extension == "csv":
        df = pd.read_csv(uploaded_file)
        extracted_text = df.to_string()

    elif file_extension == "txt":
        extracted_text = uploaded_file.read().decode("utf-8")

    elif file_extension in ["jpg", "png"]:
        img = Image.open(uploaded_file)
        extracted_text = pytesseract.image_to_string(img)  # Use OCR to extract text from images

    return extracted_text

# lab Analysis
genai.configure(api_key=GOOGLE_API_KEY)

def analyze_lab_report(report_text):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"You are an expert veterinary specialist with deep knowledge of poultry farming, especially layer birds. Analyze the following veterinary lab report of a layer bird and provide a comprehensive assessment.Focus on identifying health issues, possible diseases, recommended treatment and medication, nutritional deficiencies, and environmental stress factors:\n\n{report_text}"
        )
        return response.text
    except Exception as e:
        return f"Error analyzing lab report: {str(e)}"


# Poultry Farm Profit Calculator
def calculate_profit(feed_cost, medicine_cost, labor_cost, egg_sales, meat_sales):
    total_cost = feed_cost + medicine_cost + labor_cost
    total_revenue = egg_sales + meat_sales
    profit = total_revenue - total_cost
    return profit


# Poultry Disease Diagnosis using Gemini Vision API
def diagnose_poultry_disease(image):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    response = model.generate_content(["Analyze this image and diagnose any poultry disease. Provide possible symptoms and treatments.", image])
    return response.text


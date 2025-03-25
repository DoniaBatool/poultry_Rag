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
import crawl4ai as c4a
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


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
    
# Function to fetch latest egg prices from eggrates.pk used crawl4ai
def get_egg_prices():
    url = "https://eggrates.pk/"

    try:
        # ✅ Setup Selenium WebDriver (Headless Mode for Faster Scraping)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # ✅ Load the website
        driver.get(url)
        time.sleep(3)  # Wait for content to load

        # ✅ Extract page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()  # Close the browser

        # ✅ Find all tables with egg prices
        egg_prices = []
        tables = soup.find_all("table", class_="kb-table")

        for table in tables:
            # Get the city name from the preceding <h3> tag
            city_heading = table.find_previous("h3")
            city = city_heading.text.strip() if city_heading else "Unknown City"

            city_data = {"City": city, "Prices": []}
            rows = table.find_all("tr")

            # Extract price details from the table
            for row in rows[1:]:  # Skip the header row
                columns = row.find_all("td")
                if len(columns) >= 2:
                    quantity = columns[0].text.strip()
                    price = columns[1].text.strip()
                    city_data["Prices"].append({"Quantity": quantity, "Price": price})

            egg_prices.append(city_data)

        return egg_prices if egg_prices else ["⚠️ No relevant results found."]

    except Exception as e:
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


import streamlit as st
from utils import get_egg_prices

# Page Title
st.title("🥚 Latest Poultry Egg Rates")
st.subheader("Updated rates from [eggrates.pk](https://eggrates.pk)")

# Fetch egg prices
egg_data = get_egg_prices()

# Check if data is valid
if isinstance(egg_data, list) and egg_data and isinstance(egg_data[0], dict):
    for entry in egg_data:
        st.markdown(f"## 📍 {entry.get('City', 'Unknown City')}")  # City name as header

        # Display egg price details with default values if missing
        st.write(f"🥚 **Price Per Dozen**: {entry.get('Price Per Dozen', 'Not Available')}")
        st.write(f"🍳 **Price Per Egg**: {entry.get('Price Per Egg', 'Not Available')}")
        st.write(f"📦 **Price for 30 Eggs Tray**: {entry.get('30 Eggs Tray Price', 'Not Available')}")

        st.divider()  # Add a divider for better readability
else:
    st.error("⚠️ Unable to fetch egg price data. Please try again later.")



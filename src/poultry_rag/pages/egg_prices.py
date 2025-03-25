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

        # Display egg price details
        for price_entry in entry.get("Prices", []):
            st.write(f"📌 **{price_entry['Quantity']}** → 💰 **{price_entry['Price']} PKR**")

        st.divider()  # Add a divider for better readability
else:
    st.error("⚠️ Unable to fetch egg price data. Please try again later.")



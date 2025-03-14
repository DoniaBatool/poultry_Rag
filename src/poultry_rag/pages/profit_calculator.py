import streamlit as st
from utils import calculate_profit

st.title("📊 Poultry Farm Profit Calculator")

# User inputs
feed_cost = st.number_input("🐔 Feed Cost (PKR)", min_value=0)
medicine_cost = st.number_input("💊 Medicine Cost (PKR)", min_value=0)
labor_cost = st.number_input("👨‍🌾 Labor Cost (PKR)", min_value=0)
egg_sales = st.number_input("🥚 Egg Sales (PKR)", min_value=0)
meat_sales = st.number_input("🍗 Meat Sales (PKR)", min_value=0)

if st.button("Calculate Profit"):
    profit = calculate_profit(feed_cost, medicine_cost, labor_cost, egg_sales, meat_sales)
    st.success(f"💰 Your Poultry Farm Profit: PKR {profit}")

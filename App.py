import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# 🔹 Replace this with your Zapier Webhook URL
ZAPIER_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/"

# 🔹 Define tickers to monitor in real-time
monitored_tickers = ["SPY", "^VIX", "^TNX"]

# 🔹 Function to fetch real-time market data
def fetch_real_time_data(tickers):
    data = {}
    try:
        live_data = yf.download(tickers, period="1d", interval="5m", auto_adjust=True)
        for ticker in tickers:
            if "Close" in live_data.columns:
                data[ticker] = live_data["Close"].iloc[-1]
    except Exception as e:
        st.error(f"Error fetching real-time data: {e}")
    return data

# 🔹 Function to send email alerts via Zapier Webhook
def send_email_alert(subject, message):
    payload = {"subject": subject, "message": message}
    response = requests.post(ZAPIER_WEBHOOK_URL, json=payload)
    return response.status_code

# 🔹 Function to analyze market conditions & trigger alerts
def analyze_market_conditions(data):
    alerts = []
    signal = "Neutral"

    # Get latest market data
    spy_price = data.get("SPY", 0)
    vix = data.get("^VIX", 0)
    tnx = data.get("^TNX", 0) / 10.0  # Convert to percentage

    # Market Triggers
    if spy_price > spy_price * 1.002:  # Adjusted 200DMA placeholder logic
        if vix < 15 and tnx < 3:
            signal = "Bullish"
            alerts.append("📈 **Bullish Market**: Favor equities (90% stocks, 10% bonds).")
    elif spy_price < spy_price * 0.998:  # Adjusted 200DMA placeholder logic
        if vix > 25 and tnx > 4.5:
            signal = "Bearish"
            alerts.append("📉 **Bearish Market**: Reduce equities (40% stocks, 60% bonds).")
    else:
        alerts.append("⚖️ **Neutral Market**: Maintain balance (70% stocks, 30% bonds).")

    return signal, alerts

# 🔹 Streamlit App Layout
st.title("📡 AI-Driven Market Alert System")

# 🔹 Fetch real-time data
st.subheader("Live Market Data")
real_time_prices = fetch_real_time_data(monitored_tickers)
if real_time_prices:
    st.dataframe(pd.DataFrame(real_time_prices.items(), columns=["Ticker", "Latest Price"]))

# 🔹 Analyze market conditions
signal, alerts = analyze_market_conditions(real_time_prices)

# 🔹 Display alerts
st.subheader("📊 Market Alerts & Signals")
for alert in alerts:
    st.warning(alert)

# 🔹 Send email notification if a major shift occurs
if signal != "Neutral":
    alert_message = f"🚨 Market Alert: {signal} signal detected. {alerts[0]}"
    
    # Send Email Alert
    email_status = send_email_alert(f"Market Alert: {signal}", alert_message)

    st.write(f"📩 Email Status: {email_status}")

# 🔹 Refresh Button to manually update
if st.button("🔄 Refresh Market Data"):
    st.experimental_rerun()
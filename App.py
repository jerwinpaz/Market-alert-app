import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 🔹 Define tickers to monitor in real-time
monitored_tickers = ["SPY", "^VIX", "^TNX"]

# 🔹 Function to fetch real-time market data with error handling
def fetch_real_time_data(tickers):
    data = {}
    try:
        live_data = yf.download(tickers, period="1d", interval="5m", auto_adjust=True)
        for ticker in tickers:
            if "Close" in live_data.columns:
                try:
                    # Extract last price safely, handling potential issues
                    last_price = live_data["Close"][ticker].dropna().iloc[-1]
                    data[ticker] = float(last_price)  # Ensure it's a single float value
                except Exception:
                    st.warning(f"⚠️ Skipping {ticker}, issue retrieving price.")
                    data[ticker] = np.nan  # Assign NaN if price is missing
    except Exception as e:
        st.error(f"Error fetching real-time data: {e}")
    return data

# 🔹 Function to analyze market conditions & trigger alerts
def analyze_market_conditions(data):
    alerts = []
    signal = "Neutral"

    # Extract ticker values safely
    spy_price = float(data.get("SPY", np.nan))
    vix = float(data.get("^VIX", np.nan))
    tnx = float(data.get("^TNX", np.nan)) / 10.0  # Convert to percentage

    # Market Triggers
    if not np.isnan(spy_price) and not np.isnan(vix) and not np.isnan(tnx):
        if spy_price > spy_price * 1.002:
            if vix < 15 and tnx < 3:
                signal = "Bullish"
                alerts.append("📈 **Bullish Market**: Favor equities (90% stocks, 10% bonds).")
        elif spy_price < spy_price * 0.998:
            if vix > 25 and tnx > 4.5:
                signal = "Bearish"
                alerts.append("📉 **Bearish Market**: Reduce equities (40% stocks, 60% bonds).")
        else:
            alerts.append("⚖️ **Neutral Market**: Maintain balance (70% stocks, 30% bonds).")
    else:
        alerts.append("⚠️ **Market Data Issue**: Some prices missing, unable to generate signal.")

    return signal, alerts

# 🔹 Streamlit App Layout
st.title("📡 AI-Driven Market Alert System")

# 🔹 Fetch real-time data
st.subheader("📊 Live Market Data")
real_time_prices = fetch_real_time_data(monitored_tickers)

# ✅ Fix: Convert real-time data into a clean DataFrame & handle missing values
if real_time_prices:
    df = pd.DataFrame(list(real_time_prices.items()), columns=["Ticker", "Latest Price"])
    df["Latest Price"] = pd.to_numeric(df["Latest Price"], errors="coerce").fillna(0)
    st.dataframe(df)

# 🔹 Analyze market conditions
signal, alerts = analyze_market_conditions(real_time_prices)

# 🔹 Display alerts directly in the app
st.subheader("📢 Active Alerts")
for alert in alerts:
    if "Bullish" in alert:
        st.success(alert)  # Green for bullish
    elif "Bearish" in alert:
        st.error(alert)  # Red for bearish
    else:
        st.warning(alert)  # Neutral (gray)

# 🔹 Alert Log: Keep track of previous alerts
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []

# Add new alert to the log
st.session_state.alert_log.append(f"{signal} - {alerts[0]}")

# Display the last 5 alerts
st.subheader("📜 Recent Alerts")
for log in st.session_state.alert_log[-5:]:  # Show last 5 alerts
    st.write(log)

# 🔹 Refresh Button to manually update
if st.button("🔄 Refresh Market Data"):
    st.experimental_rerun()
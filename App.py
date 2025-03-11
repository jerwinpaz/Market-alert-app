import streamlit as st
import yfinance as yf
import numpy as np

# Define tickers to track
tickers = {
    "S&P 500": "^GSPC",
    "Russell 1000 Growth": "IWF",
    "VIX": "^VIX",
    "10Yr Bond Yield": "^TNX",
    "Gold": "GLD",
    "Tech Sector": "XLK",
    "Defensive Sector": "XLU",
}

# Function to get market data
def get_market_data(ticker):
    data = yf.download(ticker, period="6mo", interval="1d")["Close"]
    return data

# Fetch market data
market_data = {key: get_market_data(ticker) for key, ticker in tickers.items()}

# Calculate signals
def calculate_signals(data):
    signals = {}
    signals["S&P 500 Above 200DMA"] = data["S&P 500"][-1] > data["S&P 500"].rolling(200).mean()[-1]
    signals["Russell 1000 Growth 3M Change"] = (data["Russell 1000 Growth"][-1] - data["Russell 1000 Growth"][-63]) / data["Russell 1000 Growth"][-63]
    signals["VIX Above 25"] = data["VIX"][-1] > 25
    signals["Gold Strength"] = data["Gold"][-1] > data["Gold"].rolling(50).mean()[-1]
    signals["Bond Yield Spike"] = data["10Yr Bond Yield"][-1] > data["10Yr Bond Yield"].rolling(50).mean()[-1]
    signals["Tech Outperforming Defensive"] = data["Tech Sector"][-1] > data["Defensive Sector"][-1]
    return signals

# Generate signals
signals = calculate_signals(market_data)

# Streamlit UI
st.title("📈 AI-Driven Market Alert Dashboard")
st.markdown("🚀 **Live Market Monitoring** – AI-driven insights for portfolio rebalancing.")

st.subheader("📊 Market Signals")
for signal, value in signals.items():
    emoji = "✅" if value else "❌"
    st.write(f"{emoji} **{signal}:** {'Yes' if value else 'No'}")

# Display latest prices
st.subheader("🔍 Market Data")
for asset, data in market_data.items():
    st.write(f"**{asset}:** ${round(data[-1], 2)}")

# Alert recommendation
st.subheader("⚠️ Suggested Portfolio Adjustment")
if signals["S&P 500 Above 200DMA"] and signals["Russell 1000 Growth 3M Change"] > 0:
    st.success("✅ Market is in a **strong uptrend**. Maintain growth exposure (IVW, QQQ, SPY).")
elif signals["VIX Above 25"]:
    st.warning("🚨 High volatility detected! Consider shifting **20-30% to defensive assets (TLT, GLD, XLU).**")
elif not signals["S&P 500 Above 200DMA"]:
    st.error("🔴 Market trend is bearish. Reduce risk exposure & increase defensive positions.")

st.markdown("📩 **Want notifications?** Use [IFTTT](https://ifttt.com) to set up SMS/email alerts!")

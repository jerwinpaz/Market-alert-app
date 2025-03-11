import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Title and description
st.title("AI-Driven Market Alert Portfolio Dashboard")
st.write(
    "This app monitors a portfolio of assets and key market indicators, using an AI-driven strategy to alert you when market conditions suggest adjusting your portfolio allocation."
)

# Define portfolio components and market indicators
portfolio_stocks = ["AAPL", "MSFT"]  # Individual stocks
portfolio_equity_etfs = ["SPY", "QQQ", "IWM", "EEM"]  # Equity indices / ETFs
sector_etfs = ["XLE", "XLB", "XLI", "XLY", "XLV", "XLF", "XLK", "XLC", "XLRE", "XLU", "XLP"]  # Sector ETFs
bond_etfs = ["TLT"]  # Treasury bond ETF (20+ Year)
commodity_etfs = ["GLD"]  # Gold ETF
market_indicators = ["^VIX", "^TNX"]  # Volatility Index (VIX) and 10-Year Treasury Yield index

# Combine all tickers for data fetching
all_tickers = portfolio_stocks + portfolio_equity_etfs + sector_etfs + bond_etfs + commodity_etfs + market_indicators

# Define date range for historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=600)  # Approx. last 600 days (~2 years of data)

# Use caching to avoid redundant data fetches
import time
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data(tickers, start, end, retries=3, delay=5):
    """Fetches market data from Yahoo Finance with error handling."""
    for attempt in range(retries):
        try:
            data = yf.download(tickers, start=start, end=end, auto_adjust=False)

            # Flatten MultiIndex columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(1)

            # Print available columns for debugging
            print("Available columns:", data.columns)

            return data  # ✅ Return full dataframe

        except Exception as e:
            print(f"Error fetching data (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)  # Wait before retrying

    print("❌ Failed to fetch data after multiple attempts.")
    return pd.DataFrame()  # Return empty DataFrame if fetch fails
# Refresh button to manually update data
if st.button("🔄 Refresh Data"):
    load_data.clear()   # Clear cached data
    st.rerun()

# Load data (using cache if available)
prices = load_data(all_tickers, start_date, end_date)

# Calculate 200-day moving average for each asset
ma200 = prices.rolling(window=200).mean()

# Get the latest price and 200-day MA for each ticker
latest_prices = prices.iloc[-1]
latest_ma200 = ma200.iloc[-1]

# Function to determine momentum status relative to 200-day MA
def momentum_status(ticker):
    price = latest_prices[ticker]
    ma = latest_ma200[ticker]
    if pd.isna(ma):
        return "No data"
    if price >= ma:
        diff = (price - ma) / ma * 100
        return f"🔺 Above 200-day MA by {diff:.1f}%"
    else:
        diff = (ma - price) / ma * 100
        return f"🔻 Below 200-day MA by {diff:.1f}%"

# Portfolio overview & momentum signals
st.header("Portfolio Overview & Momentum Signals")

st.subheader("Stocks")
for ticker in portfolio_stocks:
    st.write(f"{ticker}: Price ${latest_prices[ticker].iloc[-1]:.2f} — {momentum_status(ticker)}")

st.subheader("Equity Indices / ETFs")
for ticker in portfolio_equity_etfs:
    st.write(f"{ticker}: Price ${latest_prices[ticker]:.2f} — {momentum_status(ticker)}")

st.subheader("Bonds & Commodities")
for ticker in bond_etfs + commodity_etfs:
    st.write(f"{ticker}: Price ${latest_prices[ticker]:.2f} — {momentum_status(ticker)}")

# AI-driven alerts for portfolio adjustments
st.header("AI-Driven Alerts & Portfolio Adjustments")
alerts = []

# Momentum-based alerts using SPY as a broad market proxy
spy_price = latest_prices.get("SPY")
spy_ma = latest_ma200.get("SPY")
if spy_price is not None and not pd.isna(spy_ma):
    if spy_price < spy_ma:
        alerts.append("SPY **fell below** its 200-day moving average. This signals weakening market momentum.")
    else:
        alerts.append("SPY **remains above** its 200-day moving average, signaling continued strength.")

# Volatility (VIX) alerts
vix_level = latest_prices["^VIX"]
if vix_level > 20:
    if vix_level >= 30:
        alerts.append(f"Market volatility is **very high** (VIX ≈ {vix_level:.1f}). Consider hedging.")
    else:
        alerts.append(f"Market volatility is elevated (VIX ≈ {vix_level:.1f}). Caution advised.")

# Bond yield alerts
tnx_index = latest_prices["^TNX"]
ten_year_yield = tnx_index / 10.0
if ten_year_yield >= 4.0:
    alerts.append(f"10-Year Treasury yield is **{ten_year_yield:.2f}%**, which may pressure equities.")

# Sector leadership alerts (Discretionary vs Staples)
xly_above = latest_prices.get("XLY", 0) >= latest_ma200.get("XLY", float('nan'))
xlp_above = latest_prices.get("XLP", 0) >= latest_ma200.get("XLP", float('nan'))
if xly_above and not xlp_above:
    alerts.append("Consumer Discretionary (XLY) is strong, suggesting **Risk-On** sentiment.")
elif xlp_above and not xly_above:
    alerts.append("Consumer Staples (XLP) is outperforming, signaling **Risk-Off** positioning.")

# Safe-haven bond alert
tlt_price = latest_prices.get("TLT")
tlt_ma = latest_ma200.get("TLT")
if tlt_price is not None and spy_price is not None and not pd.isna(tlt_ma) and not pd.isna(spy_ma):
    if tlt_price > tlt_ma and spy_price < spy_ma:
        alerts.append("Treasury bonds (TLT) are in an uptrend while equities are weak – a possible flight to safety.")

# Display alerts
if alerts:
    for alert in alerts:
        if "Risk-Off" in alert or "caution" in alert or "pressure" in alert:
            st.warning("🔔 " + alert)
        else:
            st.success("🔔 " + alert)
else:
    st.info("✅ No immediate alerts. The portfolio aligns with current market conditions.")
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
bond_etfs = ["TLT"]    # Treasury bond ETF (20+ Year)
commodity_etfs = ["GLD"]  # Gold ETF
# Market indicators (not directly in portfolio allocation)
market_indicators = ["^VIX", "^TNX"]  # Volatility Index (VIX) and 10-Year Treasury Yield index

# Combine all tickers for data fetching
all_tickers = portfolio_stocks + portfolio_equity_etfs + sector_etfs + bond_etfs + commodity_etfs + market_indicators

# Define date range for historical data (to compute 200-day moving averages)
end_date = datetime.now()
start_date = end_date - timedelta(days=600)  # approx. last 600 days (~2 years of data)

# Use caching to avoid redundant data fetches
@st.cache_data(ttl=3600)  # cache data for 1 hour
def load_data(tickers, start, end):
    # Fetch adjusted close prices for the given tickers and date range
    data = yf.download(tickers, start=start, end=end)
    return data["Adj Close"]

# Refresh button to manually update data
if st.button("🔄 Refresh Data"):
    load_data.clear()   # clear cached data
    st.experimental_rerun()

# Load data (using cache if available)
prices = load_data(all_tickers, start_date, end_date)

# Calculate 200-day moving average for each asset
ma200 = prices.rolling(window=200).mean()

# Get the latest price and 200-day MA for each ticker
latest_prices = prices.iloc[-1]
latest_ma200 = ma200.iloc[-1]

# Helper function to determine momentum status relative to 200-day MA
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

# Portfolio overview and momentum signals
st.header("Portfolio Overview & Momentum Signals")

# Stocks
st.subheader("Stocks")
for ticker in portfolio_stocks:
    st.write(f"{ticker}: Price ${latest_prices[ticker]:.2f} — {momentum_status(ticker)}")

# Equity Indices / ETFs
st.subheader("Equity Indices / ETFs")
for ticker in portfolio_equity_etfs:
    st.write(f"{ticker}: Price ${latest_prices[ticker]:.2f} — {momentum_status(ticker)}")

# Bonds and Commodities
st.subheader("Bonds & Commodities")
for ticker in bond_etfs + commodity_etfs:
    st.write(f"{ticker}: Price ${latest_prices[ticker]:.2f} — {momentum_status(ticker)}")

# Sector ETFs momentum
st.subheader("Sector Performance (200-day Momentum)")
sectors_above = 0
for sec in sector_etfs:
    status = momentum_status(sec)
    # Count how many sectors are above their 200-day MA
    if status.startswith("🔺"):
        sectors_above += 1
    st.write(f"{sec}: {status}")
# Display breadth summary
st.write(f"**Sectors above 200-day MA:** {sectors_above} / {len(sector_etfs)}")

# Key market risk indicators
st.header("Market Risk Indicators")

# Volatility Index (VIX)
vix_level = latest_prices["^VIX"]
vix_status = momentum_status("^VIX")
st.write(f"**VIX (Volatility Index):** {vix_level:.2f} — {vix_status}")

# 10-Year Treasury Yield (TNX)
tnx_index = latest_prices["^TNX"]
ten_year_yield = tnx_index / 10.0  # ^TNX is in tenths of a percent (e.g., 40 = 4.0%)
yield_status = "No data"
if not pd.isna(latest_ma200["^TNX"]):
    yield_status = "Above 200-day average 📈" if tnx_index >= latest_ma200["^TNX"] else "Below 200-day average 📉"
st.write(f"**10-Year Treasury Yield:** {ten_year_yield:.2f}% — {yield_status}")

# Sector relative strength example: Consumer Discretionary vs Consumer Staples
if "XLY" in prices.columns and "XLP" in prices.columns and len(prices) > 63:
    xly_return_3m = (prices["XLY"].iloc[-1] / prices["XLY"].iloc[-63] - 1) * 100
    xlp_return_3m = (prices["XLP"].iloc[-1] / prices["XLP"].iloc[-63] - 1) * 100
    st.write(f"**3-Month Returns:** XLY (Discretionary) {xly_return_3m:.1f}%, XLP (Staples) {xlp_return_3m:.1f}%")
    if xly_return_3m >= xlp_return_3m:
        st.write("∙ Cyclical sectors are **outperforming** defensive sectors (indicative of **Risk-On** sentiment).")
    else:
        st.write("∙ Defensive sectors are **outperforming** cyclicals (indicative of **Risk-Off** sentiment).")

# AI-driven alerts for portfolio adjustments
st.header("AI-Driven Alerts & Portfolio Adjustments")
alerts = []

# 1. Momentum-based alerts (using SPY as a broad market proxy)
spy_price = latest_prices.get("SPY")
spy_ma = latest_ma200.get("SPY")
if spy_price is not None and not pd.isna(spy_ma):
    if spy_price < spy_ma:
        # SPY trading below its 200-day MA (downtrend)
        if prices["SPY"].iloc[-2] >= ma200["SPY"].iloc[-2]:
            alerts.append("SPY **fell below** its 200-day moving average. This momentum shift suggests increasing caution on equities.")
        else:
            alerts.append("SPY remains below its 200-day moving average, indicating continued weak momentum for equities.")
    else:
        # SPY trading above its 200-day MA (uptrend)
        if prices["SPY"].iloc[-2] < ma200["SPY"].iloc[-2]:
            alerts.append("SPY **climbed back above** its 200-day moving average, signaling improving momentum. Consider increasing equity exposure.")
        # (If SPY has been above for a while, no new alert is added to avoid repetition.)

# 2. Volatility (VIX) alerts
if vix_level > 20:
    if vix_level >= 30:
        alerts.append(f"Market volatility is **very high** (VIX ≈ {vix_level:.1f}). Consider hedging or reducing risk exposure.")
    else:
        alerts.append(f"Market volatility is elevated (VIX ≈ {vix_level:.1f}). Caution is advised with risk assets.")

# 3. Bond yield alerts
if ten_year_yield >= 4.0:
    alerts.append(f"10-Year Treasury yield is **{ten_year_yield:.2f}%**, which is relatively high. High rates can pressure stocks and make bonds more attractive.")
# (If yields were dropping sharply in a crisis, that could be a separate alert for flight-to-safety, but not included here.)

# 4. Sector breadth alerts
if sectors_above <= 3:
    alerts.append(f"Only **{sectors_above} of 11** sectors are above their 200-day MA. Market breadth is very weak, reflecting a **Risk-Off** environment.")
elif sectors_above >= 8:
    alerts.append(f"**{sectors_above} of 11** sectors are above their 200-day MA. Market breadth is strong, reflecting a broad **Risk-On** rally.")

# 5. Sector leadership alerts (Discretionary vs Staples)
xly_above = latest_prices.get("XLY", 0) >= latest_ma200.get("XLY", float('nan'))
xlp_above = latest_prices.get("XLP", 0) >= latest_ma200.get("XLP", float('nan'))
if xly_above and not xlp_above:
    alerts.append("Consumer Discretionary (XLY) is strong while Staples (XLP) lag, indicating investors are leaning **Risk-On**.")
elif xlp_above and not xly_above:
    alerts.append("Consumer Staples (XLP) is outperforming XLY, indicating a shift to **Risk-Off** defensive positioning.")

# 6. Safe-haven bond alert (if Treasuries strong while equities weak)
tlt_price = latest_prices.get("TLT")
tlt_ma = latest_ma200.get("TLT")
if tlt_price is not None and spy_price is not None and not pd.isna(tlt_ma) and not pd.isna(spy_ma):
    if tlt_price > tlt_ma and spy_price < spy_ma:
        alerts.append("Treasury bonds (TLT) are in an uptrend while equities are weak – a possible flight to safety into bonds.")

# Display each alert with appropriate highlighting
if alerts:
    for alert in alerts:
        # Use warning for risk-off/caution alerts and success for positive/risk-on alerts
        if any(word in alert.lower() for word in ["caution", "weak", "risk-off", "high", "lag", "pressure", "hedging", "very high"]):
            st.warning("🔔 " + alert)
        else:
            st.success("🔔 " + alert)
else:
    st.info("✅ No immediate alerts. The portfolio aligns with current market conditions.")
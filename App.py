import streamlit as st
import yfinance as yf
from datetime import datetime
import pytz
import time

# Page configuration
st.set_page_config(page_title="Portfolio Tracker", layout="wide")

# Portfolio definition: tickers with optional target and stop-loss levels
portfolio = {
    "AAPL": {"shares": 10, "target_price": 180.0, "stop_loss": 130.0},
    "MSFT": {"shares": 5, "target_price": 320.0, "stop_loss": 250.0},
    # Add more holdings as needed, for example:
    # "GOOGL": {"shares": 8, "target_price": 150.0, "stop_loss": 100.0}
}

# Improved market data fetch function
@st.cache_data(ttl=30)  # cache results for 30 seconds to avoid excessive API calls
def get_market_data(ticker: str):
    """Fetch current market data for a given ticker symbol.
    Returns a dictionary with price, previous close, daily change, percent change, and key indicators."""
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info

    # Determine if market is currently open (using NYSE regular hours as reference)
    eastern = pytz.timezone("America/New_York")
    now_eastern = datetime.now(eastern)
    market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)
    if now_eastern.weekday() >= 5 or now_eastern < market_open or now_eastern >= market_close:
        # Market is closed (weekend or outside trading hours) – use last closing price
        current_price = info.get("previousClose")
    else:
        # Market is open – try to get live price
        current_price = info.get("regularMarketPrice")
        if current_price is None:
            # Fallback in case live price is not available
            current_price = info.get("previousClose")
    
    prev_close = info.get("previousClose")
    change = None
    pct_change = None
    if current_price is not None and prev_close is not None:
        change = current_price - prev_close
        if prev_close != 0:
            pct_change = (change / prev_close) * 100

    # Key financial indicators
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    market_cap = info.get("marketCap")
    dividend_yield = info.get("dividendYield")

    return {
        "price": current_price,
        "previous_close": prev_close,
        "change": change,
        "pct_change": pct_change,
        "pe_ratio": pe_ratio,
        "market_cap": market_cap,
        "dividend_yield": dividend_yield
    }

# App title and description
st.title("Live Portfolio Tracker")
st.caption("Real-time market data and alerts for your investment portfolio.")

# Placeholder for dynamic content (for real-time updates)
placeholder = st.empty()
refresh_interval = 30  # seconds between data refreshes

# Main loop for live updating
while True:
    # Fetch latest data for all tickers in the portfolio
    all_data = {ticker: get_market_data(ticker) for ticker in portfolio.keys()}

    # Render the dashboard inside the placeholder container
    with placeholder.container():
        # Display last update time
        st.subheader(f"Market Data (Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        
        # Show current price and daily change for each stock as metrics
        if all_data:
            cols = st.columns(len(all_data))
            for (ticker, data), col in zip(all_data.items(), cols):
                price = data["price"]
                change = data["change"]
                pct_change = data["pct_change"]
                if price is None:
                    col.metric(label=ticker, value="N/A")
                else:
                    # Format delta string with sign and percentage if available
                    if change is None or pct_change is None:
                        col.metric(label=ticker, value=f"${price:.2f}")
                    else:
                        delta_str = f"{change:+.2f} ({pct_change:+.2f}%)"
                        col.metric(label=ticker, value=f"${price:.2f}", delta=delta_str)
        else:
            st.write("Your portfolio is empty. Add some tickers to get started.")

        # Expandable section for detailed financial indicators
        with st.expander("View key financial indicators for each stock"):
            for ticker, data in all_data.items():
                st.markdown(f"**{ticker}**")
                if data["price"] is not None:
                    st.write(f"Price: ${data['price']:.2f}")
                else:
                    st.write("Price: N/A")
                if data["change"] is not None and data["pct_change"] is not None:
                    st.write(f"Daily Change: {data['change']:+.2f} ({data['pct_change']:+.2f}%)")
                else:
                    st.write("Daily Change: N/A")
                if data["pe_ratio"] is not None:
                    st.write(f"P/E Ratio: {data['pe_ratio']:.2f}")
                else:
                    st.write("P/E Ratio: N/A")
                if data["market_cap"] is not None:
                    mc = data["market_cap"]
                    # Format market cap into a human-readable string
                    if mc >= 1e12:
                        mc_str = f"{mc/1e12:.2f} Trillion"
                    elif mc >= 1e9:
                        mc_str = f"{mc/1e9:.2f} Billion"
                    elif mc >= 1e6:
                        mc_str = f"{mc/1e6:.2f} Million"
                    else:
                        mc_str = str(mc)
                    st.write(f"Market Cap: {mc_str}")
                else:
                    st.write("Market Cap: N/A")
                if data["dividend_yield"] is not None:
                    st.write(f"Dividend Yield: {data['dividend_yield']*100:.2f}%")
                else:
                    st.write("Dividend Yield: N/A")
                st.markdown("---")  # separator line between stocks

        # Portfolio alerts for target price or stop-loss triggers
        st.subheader("Portfolio Alerts")
        alerts_triggered = False
        for ticker, info in portfolio.items():
            data = all_data.get(ticker, {})
            current_price = data.get("price")
            if current_price is None:
                continue  # skip if no data for this ticker
            
            target = info.get("target_price")
            stop = info.get("stop_loss")
            if target is not None and current_price >= target:
                st.warning(f"**{ticker}** has reached or exceeded its target price of ${target:.2f}. Consider rebalancing or taking profits.")
                alerts_triggered = True
            if stop is not None and current_price <= stop:
                st.error(f"**{ticker}** has fallen to or below the stop-loss level of ${stop:.2f}. Consider reducing your position or re-evaluating this investment.")
                alerts_triggered = True
            # Example alert: significant single-day price movement
            if data.get("pct_change") is not None and abs(data["pct_change"]) >= 5:
                st.info(f"**{ticker}** moved more than 5% today. Check for news or notable events driving this change.")
                alerts_triggered = True

        if not alerts_triggered:
            st.write("No alerts at this time.")
    # Wait for the next refresh cycle
    time.sleep(refresh_interval)
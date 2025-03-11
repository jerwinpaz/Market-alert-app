import yfinance as yf
import streamlit as st

def get_market_data(symbol):
    """Fetch current market data (live price if available, else last close) and options data."""
    try:
        ticker = yf.Ticker(symbol)
        # Try to fetch intraday data for the current trading day (1-minute interval)
        intraday_data = ticker.history(period="1d", interval="1m")
        if not intraday_data.empty:
            # Market is open or recent data is available; use the latest price
            current_price = intraday_data["Close"].iloc[-1]
        else:
            # Market is closed or no intraday data; fall back to last closing price
            last_close_data = ticker.history(period="1d")  # 1d period gives the latest trading day's data
            current_price = last_close_data["Close"].iloc[-1] if not last_close_data.empty else None

        # (Optional) You can round or format current_price here if needed
        # current_price = round(current_price, 2)  # for example

        # Example additional data (if needed in the app)
        risk_free_rate = 0.05  # Placeholder risk-free rate
        options_dates = ticker.options  # Available options expiration dates

        return {
            "current_price": current_price,
            "risk_free_rate": risk_free_rate,
            "options_dates": options_dates
        }
    except Exception as e:
        st.error(f"Error fetching market data: {e}")
        return None

# Example usage within the Streamlit app:
symbol = st.text_input("Enter a stock ticker symbol:", "AAPL")
if symbol:
    data = get_market_data(symbol)
    if data:
        st.write(f"**Current Price for {symbol}:** {data['current_price']}")
        # Continue using data['risk_free_rate'] or data['options_dates'] as needed
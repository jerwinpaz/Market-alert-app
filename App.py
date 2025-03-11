import streamlit as st
import pandas as pd
import yfinance as yf
import time

# Configure the Streamlit page
st.set_page_config(page_title="Market Monitor", layout="wide")

@st.cache_data(ttl=300)
def load_data(tickers, period="1y", interval="1d"):
    """
    Fetch historical data for given ticker(s) from Yahoo Finance with retries.
    Returns a DataFrame with Date, Ticker, and OHLC (Open, High, Low, Close) and Adj Close columns.
    """
    # Ensure tickers is a list
    tickers_list = [tickers] if isinstance(tickers, str) else list(tickers)
    df = None
    # Try fetching data (up to 3 attempts for robustness)
    for attempt in range(3):
        try:
            if len(tickers_list) == 1:
                # Single ticker (use string to avoid multi-index column)
                df = yf.download(tickers_list[0], period=period, interval=interval, auto_adjust=False, threads=True)
            else:
                # Multiple tickers
                df = yf.download(tickers_list, period=period, interval=interval, auto_adjust=False, threads=True)
            # If we got data (even if partial), break out
            break
        except Exception as e:
            df = None
            if attempt < 2:
                time.sleep(1)  # wait a bit and retry
            else:
                # Final attempt failed
                print(f"Data download failed for {tickers_list}: {e}")
    # If completely failed to get data
    if df is None or df.empty:
        return pd.DataFrame()

    # Convert data to a uniform format (long form with 'Ticker' column)
    if isinstance(df.columns, pd.MultiIndex):
        # Multi-index columns (Price type, Ticker); stack tickers into rows
        df = df.stack(level=-1)
        df.index.names = ['Date', 'Ticker']
        df = df.reset_index()
    else:
        # Single ticker data, ensure 'Date' index is a column and add 'Ticker'
        df.index.name = 'Date'
        df = df.reset_index()
        if 'Ticker' not in df.columns:
            df['Ticker'] = tickers_list[0] if tickers_list else None

    # Ensure Adj Close column exists
    if 'Adj Close' not in df.columns and 'Close' in df.columns:
        df['Adj Close'] = df['Close']
    # Drop unnecessary columns
    for col in ['Dividends', 'Stock Splits']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    # Check for any tickers that might not have returned data and fetch them individually
    fetched_tickers = set(str(t).upper() for t in df['Ticker'].unique())
    missing_tickers = [t for t in (tickers_list or []) if str(t).upper() not in fetched_tickers]
    for ticker in missing_tickers:
        try:
            df_single = yf.download(ticker, period=period, interval=interval, auto_adjust=False, threads=True)
        except Exception as e:
            df_single = pd.DataFrame()
        if df_single is not None and not df_single.empty:
            df_single.index.name = 'Date'
            df_single = df_single.reset_index()
            df_single['Ticker'] = ticker
            if 'Adj Close' not in df_single.columns and 'Close' in df_single.columns:
                df_single['Adj Close'] = df_single['Close']
            for col in ['Dividends', 'Stock Splits']:
                if col in df_single.columns:
                    df_single.drop(columns=col, inplace=True)
            # Append the fetched single ticker data
            df = pd.concat([df, df_single], ignore_index=True)

    # Sort by Ticker then Date
    if 'Date' in df.columns and 'Ticker' in df.columns:
        df.sort_values(['Ticker', 'Date'], inplace=True)
    return df

# Title and description
st.title("📈 Real-Time Market Monitor")
st.write("This app fetches stock/index data and provides AI-driven alerts based on market movements.")
st.markdown("---")

# User input for ticker symbols
tickers_input = st.text_input("Enter ticker symbols (comma-separated):", value="AAPL, MSFT, GOOGL, ^VIX")
tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]

if tickers:
    data = load_data(tickers)
    if data is None or data.empty:
        st.error("No data found for the given ticker(s). Please check the symbols and try again.")
    else:
        # Warn about any tickers that had no data
        requested_set = {t.upper() for t in tickers}
        fetched_set = {str(t).upper() for t in data['Ticker'].unique()}
        missing_set = requested_set - fetched_set
        if missing_set:
            st.warning(f"Data could not be retrieved for: {', '.join(sorted(missing_set))}")

        # Show a snapshot of the latest data
        st.subheader("Latest Data")
        st.dataframe(data.tail(5))

        # Iterate through each ticker's data for individual analysis
        for ticker in data['Ticker'].unique():
            df_ticker = data[data['Ticker'] == ticker].copy()
            df_ticker.sort_values(by="Date", inplace=True)
            # Compute latest price and daily change
            latest_price = df_ticker['Adj Close'].iloc[-1] if 'Adj Close' in df_ticker.columns else df_ticker['Close'].iloc[-1]
            prev_price = df_ticker['Adj Close'].iloc[-2] if 'Adj Close' in df_ticker.columns and len(df_ticker) > 1 else None
            pct_change = None
            if prev_price is not None and prev_price != 0:
                pct_change = (latest_price - prev_price) / prev_price * 100

            # Display performance metrics
            st.subheader(f"📊 {ticker} Performance")
            st.write(f"**Latest Price:** {latest_price:,.2f}")
            if pct_change is not None:
                st.write(f"**Daily Change:** {pct_change:+.2f}%")

            # Line chart for price history
            price_col = 'Adj Close' if 'Adj Close' in df_ticker.columns else 'Close'
            st.line_chart(df_ticker.set_index('Date')[price_col])

            # AI-driven alert logic (simple example)
            alert_message = ""
            if pct_change is not None and abs(pct_change) > 5:
                direction = "📈 up" if pct_change > 0 else "📉 down"
                alert_message = f"**Alert:** {ticker} moved {direction} by {pct_change:.2f}% today, which is an unusual change."
            # (Optional) Integrate AI analysis (e.g., OpenAI API) for deeper insights
            # if "openai_api_key" in st.secrets:
            #     import openai
            #     openai.api_key = st.secrets["openai_api_key"]
            #     prompt = f"Explain possible reasons for {ticker}'s {pct_change:.2f}% move today."
            #     response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
            #     analysis = response['choices'][0]['message']['content'].strip()
            #     alert_message += f"\\nAI Analysis: {analysis}"
            if alert_message:
                st.warning(alert_message)

        st.markdown("---")
        st.caption("Data source: Yahoo Finance (via yfinance)")
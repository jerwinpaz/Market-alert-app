import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from fredapi import Fred
from textblob import TextBlob

# 🔹 OPTIONAL: Remove `newspaper3k` if errors persist
try:
    from newspaper import Article
    NEWS_ENABLED = True
except ImportError:
    NEWS_ENABLED = False

# 🔹 Replace with FRED API Key (Not required for public data)
FRED_API_KEY = "REPLACE_WITH_YOUR_KEY"
fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

# 📊 Economic Indicators
ECONOMIC_INDICATORS = {
    "Inflation (CPI)": "CPIAUCSL",
    "Fed Funds Rate": "FEDFUNDS",
    "Unemployment Rate": "UNRATE",
    "GDP Growth": "A191RL1Q225SBEA",
    "PMI (Manufacturing)": "ISMPMI"
}

# 📊 Fetch Economic Data
def get_economic_data():
    data = {}
    if fred:
        for key, series in ECONOMIC_INDICATORS.items():
            try:
                data[key] = fred.get_series_latest_n(series, 1)[0]
            except Exception:
                data[key] = "N/A"
    return data

# 📰 Fetch News Sentiment (With Error Handling)
def get_news_sentiment():
    if not NEWS_ENABLED:
        return {"Sentiment": "N/A", "Score": 0, "Headlines": ["News Scraping Disabled"]}

    url = "https://finance.yahoo.com/"
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        
        headlines = article.keywords[:5]
        sentiment_scores = [TextBlob(headline).sentiment.polarity for headline in headlines]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        sentiment_label = "Bullish" if avg_sentiment > 0 else "Bearish" if avg_sentiment < 0 else "Neutral"
        return {"Sentiment": sentiment_label, "Score": round(avg_sentiment, 3), "Headlines": headlines}

    except Exception:
        return {"Sentiment": "N/A", "Score": 0, "Headlines": ["Failed to fetch news"]}

# 📈 Fetch Market Data
def get_market_data(tickers):
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data[ticker] = stock.history(period="1d")["Close"].iloc[-1]
        except:
            data[ticker] = None
    return data

# 🔺 Market Analysis
def analyze_market_conditions(market_data, econ_data, news_sentiment):
    spy_price = market_data.get("SPY", 0)
    vix = market_data.get("^VIX", 0)
    tnx = market_data.get("^TNX", 0) / 10.0  

    inflation = econ_data.get("Inflation (CPI)", 0)
    fed_rate = econ_data.get("Fed Funds Rate", 0)
    sentiment_score = news_sentiment.get("Score", 0)

    alerts = []
    signal = "Neutral"

    if spy_price and spy_price > spy_price * 1.002:
        if vix < 15 and tnx < 3:
            signal = "Bullish"
            alerts.append("Bullish Market: Favor equities (90% stocks / 10% bonds)")
        elif vix > 30:
            signal = "High Volatility"
            alerts.append("High Volatility: Consider reducing equity exposure")

    if inflation > 4 and fed_rate > 5:
        alerts.append("🛑 Inflation Risk: Adjust bond allocation")

    if sentiment_score < -0.2:
        alerts.append("🔴 Bearish News Sentiment: Consider defensive positioning")

    return signal, alerts

# 🔹 Streamlit UI
st.title("📈 Market & Economic Alert System")

# 🎯 Fetch Data
tickers = ["SPY", "^VIX", "^TNX"]
market_data = get_market_data(tickers)
econ_data = get_economic_data()
news_sentiment = get_news_sentiment()

# 📊 Display Market Data
st.subheader("Market Data")
df_market = pd.DataFrame(market_data.items(), columns=["Ticker", "Latest Price"])
st.dataframe(df_market)

# 📊 Display Economic Data
st.subheader("Economic Indicators")
df_econ = pd.DataFrame(econ_data.items(), columns=["Indicator", "Value"])
st.dataframe(df_econ)

# 📰 Display News Sentiment
st.subheader("News Sentiment Analysis")
st.write(f"**Market Sentiment:** {news_sentiment['Sentiment']} ({news_sentiment['Score']})")
st.write("**Top Headlines:**")
for headline in news_sentiment["Headlines"]:
    st.write(f"- {headline}")

# 📊 Analyze Market Signals
signal, alerts = analyze_market_conditions(market_data, econ_data, news_sentiment)

# 🚨 Display Alerts
st.subheader("Market Alerts & Signals")
st.write(f"**Signal:** {signal}")
if alerts:
    for alert in alerts:
        st.warning(alert)
else:
    st.success("No major alerts at this time.")

# 🔄 Refresh Data Button
if st.button("🔄 Refresh Market Data"):
    st.experimental_rerun()
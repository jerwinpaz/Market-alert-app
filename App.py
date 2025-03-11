import yfinance as yf
import smtplib
from email.mime.text import MIMEText
import numpy as np

# Define market tickers to track
tickers = {
    "SP500": "^GSPC",
    "Russell1000Growth": "IWF",
    "VIX": "^VIX",
    "10YrBondYield": "^TNX",
    "Gold": "GLD",
    "TechSector": "XLK",
    "DefensiveSector": "XLU",
}

# Function to get market data
def get_market_data(ticker):
    data = yf.download(ticker, period="6mo", interval="1d")  # Get 6 months of daily data
    return data["Close"]

# Fetch latest data
market_data = {key: get_market_data(ticker) for key, ticker in tickers.items()}

# Calculate signals
def calculate_signals(data):
    signals = {}

    # Momentum indicators
    signals["SP500_Above_200DMA"] = data["SP500"][-1] > data["SP500"].rolling(200).mean()[-1]
    signals["Russell1000Growth_3M_Change"] = (data["Russell1000Growth"][-1] - data["Russell1000Growth"][-63]) / data["Russell1000Growth"][-63]

    # Volatility & risk signals
    signals["VIX_Above_25"] = data["VIX"][-1] > 25
    signals["Gold_Strength"] = data["Gold"][-1] > data["Gold"].rolling(50).mean()[-1]  # Gold above 50-day MA
    signals["Bond_Yield_Spike"] = data["10YrBondYield"][-1] > data["10YrBondYield"].rolling(50).mean()[-1]

    # Sector Strength
    signals["Tech_Leading"] = data["TechSector"][-1] > data["DefensiveSector"][-1]

    return signals

# Generate signals
signals = calculate_signals(market_data)

# Define alert logic
alert_messages = []

if not signals["SP500_Above_200DMA"]:
    alert_messages.append("🔴 S&P 500 below 200-day moving average: Consider shifting defensive.")

if signals["Russell1000Growth_3M_Change"] < -0.05:
    alert_messages.append("⚠️ Russell 1000 Growth dropped over 5% in 3 months: Risk-off.")

if signals["VIX_Above_25"]:
    alert_messages.append("🚨 VIX above 25: High volatility, shift to bonds/gold.")

if signals["Gold_Strength"]:
    alert_messages.append("🔶 Gold gaining strength: Possible risk-off move ahead.")

if signals["Bond_Yield_Spike"]:
    alert_messages.append("📈 Rising bond yields: Possible inflation fears, reduce long-duration bonds.")

if signals["Tech_Leading"]:
    alert_messages.append("🚀 Tech sector outperforming: Favor growth exposure.")

# If any alerts exist, send an email
if alert_messages:
    alert_text = "\n".join(alert_messages)

    # Email setup
    sender_email = "your_email@example.com"
    receiver_email = "your_email@example.com"
    subject = "⚠️ Market Alert: Portfolio Adjustment Suggested"
    msg = MIMEText(alert_text)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Send email (Replace with your SMTP server credentials)
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login("your_email@example.com", "your_password")
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("✅ Market alert email sent successfully.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# Print alerts to console
if alert_messages:
    print("⚡ Market Alerts Generated ⚡")
    for alert in alert_messages:
        print(alert)
else:
    print("✅ No major market alerts today.")
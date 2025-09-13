# Upstox Python Trading Bot

This project is a Python-based trading bot that uses the Upstox API to execute trades based on the "UT Bot Alerts" trading strategy.

## Description

The bot performs the following actions:
1.  Handles the secure OAuth 2.0 login flow to get an access token from Upstox.
2.  Fetches historical price data for a specified stock to initialize the trading indicators.
3.  Connects to the Upstox WebSocket to receive a live stream of market data.
4.  For each incoming price tick, it recalculates the UT Bot indicator (an ATR-based trailing stop loss).
5.  When the indicator generates a new BUY or SELL signal, it automatically places a MARKET order through the Upstox API.

**Disclaimer:** This code is for educational and demonstrational purposes only. It is not financial advice. Automated trading involves significant risk, and you should use this code at your own risk.

## Prerequisites

*   Python 3.6 or higher.
*   An active Upstox account.

## Setup Instructions

### 1. Create an Upstox Developer App

Before you can use the bot, you need to get API credentials from Upstox.

1.  Go to the [Upstox Developer Console](https://account.upstox.com/developer/apps).
2.  Create a new app.
3.  Give it a name (e.g., "MyTradingBot").
4.  For the **Redirect URI**, you **must** enter `http://127.0.0.1:8000/callback`. This is the local address the bot will use to complete the login process.
5.  After creating the app, you will receive your `API Key` and `API Secret`. Keep these safe.

### 2. Install Python Libraries

Navigate to this project directory in your terminal and install the required libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 3. Configure the Bot

Open the `trading_bot.py` file in a text editor and update the configuration section at the top:

1.  **`API_KEY`**: Replace `"YOUR_API_KEY"` with the API Key from your Upstox app.
2.  **`API_SECRET`**: Replace `"YOUR_API_SECRET"` with the API Secret from your Upstox app.
3.  **`INSTRUMENT_KEY`**: Change this to the instrument key of the stock you want to trade. The example is set to ITC. You can find the instrument keys for other stocks from the Upstox API or their official instrument master list.
4.  **`TRADE_QUANTITY`**: Set the number of shares you want to trade for each signal.

## How to Run the Bot

1.  Open your terminal and navigate to this project directory.
2.  Run the following command:
    ```bash
    python trading_bot.py
    ```
3.  The script will start a small local web server and print a login URL to the console. It will also attempt to open this URL automatically in your default web browser.
4.  Log in to your Upstox account in the browser.
5.  After successful login, you will be redirected to a blank page showing "Authentication successful!".
6.  The script running in your terminal will automatically detect this and capture the necessary `authorization_code`. It will then proceed to get the access token and start the bot.
7.  The bot will then fetch historical data, connect to the WebSocket, and start listening for live prices. You will see log messages in your terminal for new ticks and any generated trade signals.

To stop the bot, simply press `Ctrl+C` in the terminal.

## Important Notes

*   **Tick Processing:** For simplicity, this bot treats every incoming price tick as a new data point for recalculating the indicator. In a real-world, high-frequency scenario, you would typically aggregate these ticks into time-based candles (e.g., 1-minute, 5-minute) before feeding them into the indicator logic.
*   **Error Handling:** The script has basic error handling but can be improved for a production environment (e.g., by adding automatic reconnection logic for the WebSocket).

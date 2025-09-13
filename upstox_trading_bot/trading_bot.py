import os
import pandas as pd
import pandas_ta as ta
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Import Upstox and WebSocket libraries - will use the official SDK
import upstox_client
from upstox_client.api import login_api
from upstox_client.api import order_api
from upstox_client.api import websocket_api
from upstox_client.models import MarketDataFeed, MarketDataFeedV3

# --- CONFIGURATION ---
# TODO: Fill in your API Key and API Secret from the Upstox Developer Console
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
REDIRECT_URI = "http://127.0.0.1:8000/callback" # Must match the one in your Upstox app

# --- TRADING PARAMETERS ---
# TODO: Set the instrument key for the stock you want to trade
# You can find this using the Upstox API or from their instrument master list
INSTRUMENT_KEY = "NSE_EQ|INE669E01016" # Example: ITC
TRADE_QUANTITY = 1
ATR_PERIOD = 10
ATR_MULTIPLIER = 1.0 # This is the 'a' value from your UT Bot script

# --- AUTHENTICATION & SERVER ---
auth_code = None
server_thread = None

class AuthHandler(BaseHTTPRequestHandler):
    """A simple HTTP server to handle the OAuth callback."""
    def do_GET(self):
        global auth_code
        if '/callback' in self.path:
            auth_code = self.path.split('code=')[1].split('&')[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authentication successful! You can close this window.")
            print(f"\nReceived auth code: {auth_code}")
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    """Starts the local HTTP server in a separate thread."""
    global server_thread
    server = HTTPServer(('localhost', 8000), AuthHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Local server started on port 8000 to handle OAuth callback.")

class UpstoxTrader:
    def __init__(self):
        self.api_client = None
        self.access_token = None
        self.ws = None
        self.historical_data = pd.DataFrame()
        self.atr_trailing_stop = 0.0
        self.position = 0  # -1 for short, 1 for long, 0 for neutral
        self.is_processing = False # To prevent race conditions

    def run(self):
        print("Starting Upstox Trading Bot...")
        self.login()

        if self.access_token:
            print("\nLogin successful. Access token obtained.")
            self.get_historical_data()
            self.start_websocket()
        else:
            print("\nFailed to obtain access token. Exiting.")

    def login(self):
        """Handles the OAuth 2.0 login flow to get the access token."""
        global auth_code

        # 1. Start a local server to listen for the callback
        start_server()

        # 2. Generate and open the login URL
        api_instance = login_api.LoginApi()
        login_url = api_instance.authorize(client_id=API_KEY, redirect_uri=REDIRECT_URI, response_type="code")
        print(f"\nPlease open this URL in your browser to log in:\n{login_url}")
        webbrowser.open(login_url)

        # 3. Wait for the user to log in and for the auth_code to be captured
        print("\nWaiting for user authentication...")
        while auth_code is None:
            time.sleep(1)

        # 4. Exchange the auth code for an access token
        api_instance.token(
            client_id=API_KEY,
            client_secret=API_SECRET,
            redirect_uri=REDIRECT_URI,
            code=auth_code,
            grant_type='authorization_code'
        )

        # Store the access token for future API calls
        self.access_token = api_instance.api_client.configuration.access_token

        # Configure the main API client with the access token
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        self.api_client = upstox_client.ApiClient(configuration)

    def get_historical_data(self):
        """Fetches initial historical data to warm up the indicators."""
        print("\nFetching historical data...")
        try:
            api_instance = upstox_client.HistoryApi(self.api_client)
            # Fetch for the last ~30 days to ensure enough data for indicators
            api_response = api_instance.get_historical_candle_data1(
                instrument_key=INSTRUMENT_KEY,
                interval='1minute',
                to_date=time.strftime('%Y-%m-%d'),
                from_date=(pd.to_datetime(time.strftime('%Y-%m-%d')) - pd.DateOffset(days=30)).strftime('%Y-%m-%d')
            )

            candles = api_response.data.candles
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            self.historical_data = df.iloc[::-1].copy() # Reverse to have oldest first
            print("Historical data fetched successfully.")

            # Initial calculation of indicators
            self.calculate_indicators(self.historical_data)

        except Exception as e:
            print(f"Error fetching historical data: {e}")

    def _get_websocket_url(self):
        """Gets the authorized WebSocket URL from Upstox."""
        try:
            api_instance = websocket_api.WebsocketApi(self.api_client)
            api_response = api_instance.get_market_data_feed_authorize_v3()
            return api_response.data.authorized_redirect_uri
        except Exception as e:
            print(f"Error getting WebSocket URL: {e}")
            return None

    def start_websocket(self):
        """Starts the WebSocket connection in a separate thread."""
        ws_url = self._get_websocket_url()
        if not ws_url:
            print("Could not get WebSocket URL. Exiting.")
            return

        self.ws = websocket_client.WebSocketApp(ws_url,
                                                on_open=self._on_open,
                                                on_message=self._on_message,
                                                on_error=self._on_error,
                                                on_close=self._on_close)

        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        print("\nWebSocket connection started. Listening for live data...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.ws.close()

    def _on_open(self, ws):
        """Called when the WebSocket connection is opened."""
        print("WebSocket opened.")
        sub_request = {
            "guid": "1",
            "method": "sub",
            "data": {"mode": "full", "instrumentKeys": [INSTRUMENT_KEY]}
        }
        import json
        binary_message = json.dumps(sub_request).encode('utf-8')
        ws.send(binary_message, opcode=websocket.ABNF.OPCODE_BINARY)
        print(f"Subscribed to: {INSTRUMENT_KEY}")

    def _on_message(self, ws, message):
        """Called on receipt of a new message from the WebSocket."""
        if self.is_processing:
            return # Skip if already processing a tick

        self.is_processing = True
        try:
            decoded_data = MarketDataFeed.FromString(message)
            if decoded_data.type == "live_feed":
                for instrument, feed in decoded_data.feeds.items():
                    ltp = feed.ltpc.ltp

                    # NOTE: This is a simplified tick processing. For a real bot,
                    # you'd aggregate ticks into candles (e.g., 1-minute) before calculating.
                    # For this example, we'll pretend each tick is a new candle's close.

                    # Create a new row for the DataFrame
                    new_row = pd.DataFrame([{
                        'open': ltp, 'high': ltp, 'low': ltp, 'close': ltp,
                        'timestamp': pd.to_datetime('now', utc=True)
                    }]).set_index('timestamp')

                    # Append new data and recalculate
                    self.historical_data = pd.concat([self.historical_data, new_row])

                    last_position = self.position
                    self.calculate_indicators(self.historical_data)
                    new_position = self.position

                    # Check for a signal change
                    if new_position != last_position:
                        if new_position == 1:
                            print("\n--- BUY SIGNAL DETECTED ---")
                            self.place_order(transaction_type=order_api.TransactionType.BUY)
                        elif new_position == -1:
                            print("\n--- SELL SIGNAL DETECTED ---")
                            self.place_order(transaction_type=order_api.TransactionType.SELL)
        except Exception as e:
            print(f"Error processing message: {e}")
        finally:
            self.is_processing = False

    def place_order(self, transaction_type, order_type=order_api.OrderType.MARKET):
        """Places an order on Upstox."""
        if not self.api_client:
            print("API client not initialized. Cannot place order.")
            return

        print(f"Attempting to place {transaction_type.value} order for {INSTRUMENT_KEY}")
        try:
            api_instance = order_api.OrderApi(self.api_client)
            order_request = order_api.PlaceOrderRequest(
                quantity=TRADE_QUANTITY,
                product=order_api.Product.D,
                validity=order_api.Validity.DAY,
                price=0,
                instrument_token=INSTRUMENT_KEY,
                order_type=order_type,
                transaction_type=transaction_type,
                disclosed_quantity=0,
                trigger_price=0,
                is_amo=False
            )
            api_response = api_instance.place_order(body=order_request)
            print(f"Order placed successfully. Order ID: {api_response.data.order_id}")
            return api_response
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    def _on_error(self, ws, error):
        """Called on a WebSocket error."""
        print(f"WebSocket Error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Called when the WebSocket connection is closed."""
        print("WebSocket closed.")

    def calculate_indicators(self, df):
        """
        Translates the UT Bot Pine Script logic to Python.
        Calculates ATR, the ATR Trailing Stop, and the position signal.
        """
        if df.empty:
            return

        # Calculate ATR using pandas-ta
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=ATR_PERIOD)

        # Drop rows with NaN values that result from indicator calculations
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Helper function to mimic Pine Script's nz()
        def nz(value, default=0.0):
            return default if pd.isna(value) else value

        # Iteratively calculate ATR Trailing Stop
        atr_trailing_stop = [0.0] * len(df)
        position = [0] * len(df)

        for i in range(1, len(df)):
            src = df['close'].iloc[i]
            src_prev = df['close'].iloc[i-1]
            n_loss = ATR_MULTIPLIER * df['atr'].iloc[i]

            stop_prev = atr_trailing_stop[i-1]
            pos_prev = position[i-1]

            # Core ATR Trailing Stop logic
            if src > nz(stop_prev) and src_prev > nz(stop_prev):
                atr_trailing_stop[i] = max(nz(stop_prev), src - n_loss)
            elif src < nz(stop_prev) and src_prev < nz(stop_prev):
                atr_trailing_stop[i] = min(nz(stop_prev), src + n_loss)
            elif src > nz(stop_prev):
                atr_trailing_stop[i] = src - n_loss
            else:
                atr_trailing_stop[i] = src + n_loss

            # Core position signal logic
            if src_prev < nz(stop_prev) and src > nz(stop_prev):
                position[i] = 1
            elif src_prev > nz(stop_prev) and src < nz(stop_prev):
                position[i] = -1
            else:
                position[i] = nz(pos_prev)

        df['atr_trailing_stop'] = atr_trailing_stop
        df['position'] = position

        # Update the bot's state with the latest values
        if not df.empty:
            self.historical_data = df
            self.atr_trailing_stop = df['atr_trailing_stop'].iloc[-1]
            self.position = df['position'].iloc[-1]
            print(f"Latest Data Point:\n{df.tail(1)}")


if __name__ == "__main__":
    bot = UpstoxTrader()
    bot.run()

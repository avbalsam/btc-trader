import queue
import threading
import time

from binance import ThreadedWebsocketManager
from binance import Client
from hitbtc import HitBTC
from gemini import GeminiOrderBook
import cbpro


# Class which handles exchanges
class Exchange:
    """Interface implemented by all Exchanges"""

    def get_bid(self):
        pass

    def get_ask(self):
        pass

    def restart_socket(self):
        pass

    def get_stream_error(self):
        pass


class Gemini(Exchange):
    """Subclass of Exchange which handles the Gemini API"""

    def __init__(self):
        self.name = "Gemini"
        self.client = GeminiOrderBook("btcusd")
        self.client.start()
        self.socket_data = list()
        self.best_bid = float()
        self.best_ask = float()
        self.stream_error = False
        time.sleep(5)
        self.worker_thread = threading.Thread(target=self.thread_receive_socket_data)
        self.worker_thread.start()
        print("Gemini socket connected...")

    def get_bid(self):
        """
        Method to get best bid on the Gemini market.

        Returns:
            bid (float): Best bid on the Gemini market
        """
        return float(self.best_bid)

    def get_ask(self):
        """
        Method to get best ask on the Gemini market.

        Returns:
            ask (float): Best ask on the Gemini market
        """
        return float(self.best_ask)

    def restart_socket(self):
        """Restart Gemini socket by closing and creating new connection"""
        print("Restarting Gemini socket...")
        self.client.close()
        time.sleep(2)
        self.client = GeminiOrderBook("btcusd")
        self.client.start()
        print("Gemini socket restarted")

    def thread_receive_socket_data(self):
        while True:
            msg = self.client.get_market_book()
            self.socket_data = msg
            try:
                self.best_bid = self.client.get_bid()
                self.best_ask = self.client.get_ask()
                time.sleep(.08)
            except ValueError:
                pass
            except KeyError:
                print("Gemini socket error...")
                print(msg)
                self.restart_socket()

    def get_stream_error(self):
        return self.stream_error


class HitBtc(Exchange):
    """Subclass of Exchange for dealing with the HitBtc API"""

    def __init__(self):
        self.name = "HitBtc"
        self.stream_error = False
        self.socket_data = list()
        self.best_bid = float()
        self.best_ask = float()
        self.client = HitBTC()
        self.client.start()
        time.sleep(5)
        self.client.subscribe_ticker(symbol="BTCUSD")
        self.worker_thread = threading.Thread(target=self.thread_receive_socket_data)
        self.worker_thread.start()
        print("HitBtc socket connected...")

    def get_bid(self):
        """
        Method to get best bid on the HitBtc market.

        Returns:
            bid (float): Best bid on the HitBtc market
        """
        return float(self.best_bid)

    def get_ask(self):
        """
        Method to get best ask on the HitBtc market.

        Returns:
            ask (float): Best ask on the HitBtc market
        """
        return float(self.best_ask)

    def restart_socket(self):
        """Restart HitBtc socket by closing and creating new connection"""
        print("Restarting HitBtc socket...")
        self.client.stop()
        time.sleep(2)
        self.client.subscribe_ticker(symbol="BTCUSD")
        print("HitBtc socket restarted")
        self.stream_error = False

    def thread_receive_socket_data(self):
        while True:
            try:
                data = self.client.recv()
            except queue.Empty:
                time.sleep(.01)
                continue
            try:
                ticker = data[2]
                self.best_ask = ticker['ask']
                self.best_bid = ticker['bid']
                self.socket_data.append(ticker)
                time.sleep(.08)
            except (KeyError, TypeError):
                if data[0] != 'Response':
                    print("HitBtc stream error...")
                    self.stream_error = True

    def get_stream_error(self):
        return self.stream_error


class Binance(Exchange):
    """Subclass of exchange which deals with the Binance API. This API only supports conversion to USDT."""

    def __init__(self):
        """Initialize instance of Binance class without an api key"""
        self.name = "Binance"
        self.socket_data = list()
        self.best_ask = float()
        self.best_bid = float()
        self.stream_error = False

        # initialize websocket
        self.client = ThreadedWebsocketManager()
        self.client.start()
        self.conn_key = self.client.start_symbol_book_ticker_socket(callback=self.handle_ticker_socket_message,
                                                                    symbol="BTCUSDT")
        print("Binance socket connected...")

    def __init_(self, api_key, api_secret):
        """Initialize instance of Binance class using api key

        Args:
            api_key: Public key for binance api with read and transact permissions
            api_secret: Secret key for binance api with read and transact permissions
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.__init__()
        self.test_client = Client(api_key, api_secret, testnet=True)

    def restart_socket(self):
        """Restarts Binance websocket, by closing and creating new connection"""
        print("Restarting binance socket...")
        self.client.stop_socket(self.conn_key)
        time.sleep(2)
        self.conn_key = self.client.start_symbol_book_ticker_socket(callback=self.handle_ticker_socket_message,
                                                                    symbol="BTCUSDT")
        self.stream_error = False
        print("Binance socket restarted")

    def handle_ticker_socket_message(self, msg):
        self.socket_data.append(msg)
        try:
            self.best_ask = msg['a']
            self.best_bid = msg['b']
        except KeyError:
            if 'e' in msg and msg['e'] == 'error':
                print("Binance socket error...")
                self.stream_error = True

    def get_bid(self):
        """
        Method to get best bid on the Binance market.

        Returns:
            bid (float): Best bid on the Binance market
        """
        return float(self.best_bid)

    def get_ask(self):
        """
        Method to get best ask on the Binance market.

        Returns:
            ask (float): Best ask on the Binance market
        """
        return float(self.best_ask)

    def get_stream_error(self):
        return self.stream_error

    def buy_market(self, quantity):
        self.test_client.order_market_buy(symbol="BTCUSDT", quantity=quantity)

    def sell_market(self, quantity):
        self.test_client.order_market_sell(symbol="BTCUSDT", quantity=quantity)

    def get_historical_klines(self, num_days):
        data = self.test_client.get_historical_klines("BTCUSDT", self.test_client.KLINE_INTERVAL_1MINUTE,
                                                      str(num_days) + "day ago UTC")
        return data



class CoinbaseWebsocketClient(cbpro.WebsocketClient):
    def __init__(self):
        super().__init__()
        self.socket_data = list()
        self.best_bid = float()
        self.best_ask = float()
        self.stream_error = False

    """
    Class to handle coinbase websocket events
    """

    def on_open(self):
        """
        Method inherited from cbpro.WebsocketClient class which is run immediately before
        establishing websocket connection
        """
        self.url = "wss://ws-feed.pro.coinbase.com/"
        self.products = ["BTC-USD"]
        self.channels = ["ticker"]

    def on_message(self, msg):
        self.socket_data.append(msg)
        # print("Coinbase: " + str(msg))
        try:
            self.best_bid = msg['best_bid']
            self.best_ask = msg['best_ask']
        except KeyError:
            if msg['type'] != 'subscriptions':
                self.stream_error = True
                print("Coinbase stream error...")
                print(msg)

    def on_close(self):
        print("Coinbase websocket closed!")
        self.stream_error = True


class Coinbase(Exchange):
    def __init__(self):
        self.name = "Coinbase"
        self.client = CoinbaseWebsocketClient()
        self.client.start()
        print("Coinbase socket connected...")

    def get_bid(self):
        """
        Method to get best bid on the Coinbase market.

        Returns:
            bid (float): Best bid on the Coinbase market
        """
        return float(self.client.best_bid)

    def get_ask(self):
        """
        Method to get best bid on the Coinbase market.

        Returns:
            bid (float): Best bid on the Coinbase market
        """
        return float(self.client.best_ask)

    def restart_socket(self):
        print("Restarting coinbase socket...")
        self.client.close()
        time.sleep(2)
        self.client = CoinbaseWebsocketClient()
        self.client.start()
        print("Coinbase socket restarted")
        self.client.stream_error = False

    def get_stream_error(self):
        return self.client.stream_error

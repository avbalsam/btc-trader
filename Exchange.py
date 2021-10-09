import queue
import threading
import time

import cbpro
from binance import ThreadedWebsocketManager
from gemini import GeminiOrderBook
from hitbtc import HitBTC


# Class which handles exchanges
class Exchange:
    """Interface implemented by the Exchange class"""

    def api_call(self, path=''):
        pass

    def get_bid(self):
        pass

    def get_ask(self):
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

    def thread_receive_socket_data(self):
        while True:
            try:
                msg = self.client.get_market_book()
                self.socket_data.append(msg)
                # print("Gemini: " + str(msg))
                self.best_bid = self.client.get_bid()
                self.best_ask = self.client.get_ask()
                time.sleep(.08)
            except ValueError:
                pass


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

    def restart_stream(self):
        print("Restarting HitBtc socket...")
        self.client.stop()
        time.sleep(2)
        self.client.subscribe_ticker(symbol="BTCUSD")
        print("HitBtc socket restarted")

    def thread_receive_socket_data(self):
        while True:
            try:
                data = self.client.recv()
                #print(data)
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



class Binance(Exchange):
    """Subclass of exchange which deals with the Binance API. This API only supports conversion to USDT."""

    def __init__(self):
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

    def restart_stream(self):
        print("Restarting stream...")
        self.client.stop_socket(self.conn_key)
        time.sleep(2)
        self.conn_key = self.client.start_symbol_book_ticker_socket(callback=self.handle_ticker_socket_message,
                                                                    symbol="BTCUSDT")
        self.stream_error = False
        print("Binance socket restarted")

    def handle_ticker_socket_message(self, msg):
        self.connected = True
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

    def buy_market(self, quantity):
        self.client.order_market_buy(symbol="BTCUSDT", quantity=quantity)

    def sell_market(self, quantity):
        self.client.order_market_sell(symbol="BTCUSDT", quantity=quantity)

    def get_historical_klines(self, num_days):
        data = self.client.get_historical_klines("BTCUSDT", self.client.KLINE_INTERVAL_1MINUTE,
                                                 str(num_days) + "day ago UTC")
        return data


class coinbaseWebsocketClient(cbpro.WebsocketClient):
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
            print("Coinbase stream error...")
            print(msg)
            if msg['type'] != 'subscriptions':
                self.stream_error = True

    def on_close(self):
        print("Coinbase websocket closed!")


class Coinbase(Exchange):
    def __init__(self):
        self.name = "Coinbase"
        self.client = coinbaseWebsocketClient()
        self.client.start()
        print("Coinbase socket connected...")

    def get_bid(self):
        return float(self.client.best_bid)

    def get_ask(self):
        return float(self.client.best_ask)

    def restart_stream(self):
        print("Restarting coinbase socket...")
        self.client.close()
        time.sleep(2)
        self.client = coinbaseWebsocketClient()
        self.client.start()
        print("Coinbase socket restarted")

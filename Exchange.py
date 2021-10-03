import requests
import json
import robin_stocks.robinhood as r
import pyotp
from binance import Client as binance_client
from binance import ThreadedWebsocketManager
import cbpro
import threading, time, queue
from hitbtc import HitBTC


# Class which handles exchanges
class ExchangeInterface:
    """Interface implemented by the Exchange class"""

    def api_call(self, path=''):
        pass

    def get_bid(self):
        pass

    def get_ask(self):
        pass


class Exchange(ExchangeInterface):
    """Superclass to work with bitcoin exchange API handling."""

    def api_call(self, path=''):
        """
        Generic helper function to call any API endpoint

        Args:
            path (str): Full API endpoint to call
            query (str): Any additional queries to add to the API call

        Returns:
            response (str): The JSON response from the API
        """
        url = self.base_url + path
        if "{product_code}" in url:
            url = url.replace("{product_code}", self.product_code)
        response = json.loads(requests.get(url).text)
        return response

    def get_ticker(self):
        """
        Calls API to get JSON file of current buy and sell prices

        Args:
            product_code (str): Shows the API which currency to use (ex. BTC_USD)
        Returns:
            response (str): JSON response from the API which contains current prices
        """
        path = self.get_ticker_endpoint
        response = self.api_call(path)
        return response

    def get_board(self):
        """
        Calls API to get JSON file of all bids on the bitcoin market (i.e. the board)

        Returns:
            response (dict): JSON response from the API which contains all market bids
        """
        path = self.get_board_endpoint
        response = self.api_call(path)
        return response

    # TODO: Add methods to buy and sell bitcoin


class Bitflyer(Exchange):
    """Subclass of Exchange which handles the Bitflyer API"""

    def __init__(self):
        self.base_url = 'https://api.bitflyer.com/'
        self.key = None
        self.get_ticker_endpoint = 'v1/getticker?product_code={product_code}'
        self.get_board_endpoint = 'v1/board/?product_code={product_code}'
        self.product_code = 'BTC_USD'
        self.buy_endpoint = None
        self.sell_endpoint = None
        self.trading_fee = .0015

    def get_bid(self):
        """
        Method to get best bid on the Bitflyer market.

        Returns:
            bid (float): Best bid on the Bitflyer market
        """
        # print("bitflyer call")
        response = self.get_ticker()
        bid = float(response['best_bid'])
        return bid - bid * self.trading_fee

    def get_ask(self):
        """
        Method to get best ask on the Bitflyer market.

        Returns:
            ask (float): Best ask on the Bitflyer market
        """
        response = self.get_ticker()
        ask = float(response['best_ask'])
        return ask + (ask * self.trading_fee)


class ItBit(Exchange):
    """Subclass of Exchange which handles the ItBit API"""

    def __init__(self):
        self.base_url = 'https://api.itbit.com/v1/'
        self.key = None
        self.get_ticker_endpoint = 'markets/{product_code}/ticker'
        self.get_board_endpoint = 'markets/{product_code}/order_book'
        self.product_code = 'XBTUSD'
        self.buy_endpoint = None
        self.sell_endpoint = None
        self.trading_fee = .0035

    def get_bid(self):
        """
        Method to get best bid on the ItBit market.

        Returns:
            bid (float): Best bid on the ItBit market
        """
        # print("itbit call")
        response = self.get_ticker()
        bid = float(response['bid'])
        return bid - (bid * self.trading_fee)

    def get_ask(self):
        """
        Method to get best ask on the ItBit market.

        Returns:
            ask (float): Best ask on the ItBit market
        """
        response = self.get_ticker()
        ask = float(response['ask'])
        return ask


class Bittrex(Exchange):
    """Subclass of Exchange which handles the Bittrex API

    Bittrex only supports conversion from USDC, a type of cryptocurrency whose value is set at $1.00."""

    def __init__(self):
        self.base_url = 'https://api.bittrex.com/api/v1.1/'
        self.key = None
        self.get_ticker_endpoint = 'public/getticker?market={product_code}'
        self.get_board_endpoint = 'public/getorderbook?market={product_code}&type=both'
        self.product_code = 'BTC-USDC'
        self.buy_endpoint = None
        self.sell_endpoint = None
        self.trading_fee = .0030

    def get_bid(self):
        """
        Method to get best bid on the Bittrex market.

        Returns:
            bid (float): Best bid on the Bittrex market
        """
        # print("bittrex call")
        response = self.get_ticker()
        bid = float(response['result']['Bid'])
        # Take the reciprocal of the bid for consistency with the other APIs
        bid = 1 / bid
        return bid - bid * self.trading_fee

    def get_ask(self):
        """
        Method to get best ask on the Bittrex market.

        Returns:
            ask (float): Best ask on the Bittrex market
        """
        response = self.get_ticker()
        ask = float(response['result']['Bid'])
        # Take the reciprocal of the ask for consistency with the other APIs
        ask = 1 / ask
        return ask


class Gemini(Exchange):
    """Subclass of Exchange which handles the Gemini API"""

    def __init__(self):
        self.base_url = 'https://api.gemini.com/'
        self.key = None
        self.get_ticker_endpoint = 'v1/pubticker/{product_code}'
        self.get_board_endpoint = 'v1/book/{product_code}'
        self.product_code = 'btcusd'
        self.buy_endpoint = None
        self.sell_endpoint = None
        self.trading_fee = .0035

    def get_bid(self):
        """
        Method to get best bid on the Gemini market.

        Returns:
            bid (float): Best bid on the Gemini market
        """
        # print("gemini call")
        response = self.get_ticker()
        bid = float(response['bid'])
        return bid

    def get_ask(self):
        """
        Method to get best ask on the Gemini market.

        Returns:
            ask (float): Best ask on the Gemini market
        """
        response = self.get_ticker()
        ask = float(response['ask'])
        return ask


class HitBtc(Exchange):
    """Subclass of Exchange for dealing with the HitBtc API"""

    def __init__(self):
        self.socket_data = list()
        self.best_bid = float()
        self.best_ask = float()
        self.client = HitBTC()
        self.client.start()
        time.sleep(1)
        self.client.subscribe_ticker(symbol="BTCUSD")
        t = threading.Thread(target=self.thread_receive_socket_data)
        t.start()

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

    def thread_receive_socket_data(self):
        while True:
            try:
                data = self.client.recv()
                ticker = data[2]
                try:
                    self.best_ask = ticker['ask']
                    self.best_bid = ticker['bid']
                    self.socket_data.append(ticker)
                except:
                    continue
            except queue.Empty:
                continue


class Binance(Exchange):
    """Subclass of exchange which deals with the Binance API. This API only supports conversion to USDT."""

    def __init__(self):
        self.socket_data = list()
        self.best_ask = float()
        self.best_bid = float()

        # initialize websocket
        twm = ThreadedWebsocketManager()
        twm.start()
        twm.start_symbol_book_ticker_socket(callback=self.handle_ticker_socket_message, symbol="BTCUSDT")

    def handle_ticker_socket_message(self, msg):
        self.socket_data.append(msg)
        self.best_ask = msg['a']
        self.best_bid = msg['b']

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


class Robinhood(Exchange):
    def __init__(self):
        self.totp = pyotp.TOTP("NBB2XJDL2IBBSYZG").now()
        r.login("Avbalsam", "Avrahamthegreat1@", mfa_code=self.totp)

    def get_bid(self):
        # print("rb call")
        return float(r.get_crypto_quote("BTC", "bid_price"))

    def get_ask(self):
        return float(r.get_crypto_quote("BTC", "ask_price"))

"""
class Bitmex(Exchange):
    def __init__(self):
        self.api_key = "nii8W8iDzk4EQXAgNBk6FIAT"
        self.api_secret = "yoTgMAeHxqV91p98JSEqV8G26AkMm7M5v3QHaSI-qQQVlyhd"
        self.client = bitmex.bitmex(test=False, api_key=self.api_key, api_secret=self.api_secret)

    def get_ask(self):
        response = requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()
        return response[0]['price']

    def get_bid(self):
        response = requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()
        return response[1]['price']
"""

class coinbaseWebsocketClient(cbpro.WebsocketClient):
    def __init__(self):
        super().__init__()
        self.socket_data = None
        self.best_ask = None
        self.best_bid = None

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
        self.socket_data = list()
        self.best_bid = float()
        self.best_ask = float()

    def on_message(self, msg):
        self.socket_data.append(msg)
        try:
            self.best_bid = msg['best_bid']
            self.best_ask = msg['best_ask']
        except KeyError:
            pass

    def on_close(self):
        print("Coinbase websocket closed!")


class Coinbase(Exchange):
    def __init__(self):
        self.client = coinbaseWebsocketClient()
        self.client.start()

    def get_bid(self):
        return float(self.client.best_bid)

    def get_ask(self):
        return float(self.client.best_ask)

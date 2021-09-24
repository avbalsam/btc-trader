import requests
import json
import robin_stocks.robinhood as r
import pyotp
import bitmex
from binance import Client as binance_client
from coinbase.wallet.client import Client as coinbase_client


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
        #print("bitflyer call")
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
        #print("itbit call")
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
        #print("bittrex call")
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
        #print("gemini call")
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
        self.base_url = "https://api.hitbtc.com/"
        self.get_ticker_endpoint = 'api/2/public/ticker/{product_code}'
        self.get_board_endpoint = "api/2/public/orderbook/{product_code}"
        self.product_code = 'BTCUSD'
        self.buy_endpoint = None
        self.sell_endpoint = None
        self.trading_fee = .002

    def get_bid(self):
        """
        Method to get best bid on the HitBtc market.

        Returns:
            bid (float): Best bid on the HitBtc market
        """
        #print("hitbtc call")
        response = self.get_ticker()
        bid = float(response['bid'])
        return bid

    def get_ask(self):
        """
        Method to get best ask on the HitBtc market.

        Returns:
            ask (float): Best ask on the HitBtc market
        """
        response = self.get_ticker()
        ask = float(response['ask'])
        return ask


class Binance(Exchange):
    """Subclass of exchange which deals with the Binance API. This API only supports conversion to TUSD."""

    def __init__(self):
        self.base_url = 'https://www.binance.com/'
        self.key = "aN5UaSppjZo1aph321encNJbeTYzfPSIkwERtDQdH7mDhm532NuPeuMisjtp2JmU"
        self.secret = "GaIUogqTeOMdfQGRDEOsyt6GrpIYP270AVw60c2odfo4pQFhMzXLhFa0gq4LJuWk"
        self.get_ticker_endpoint = 'api/v3/ticker/bookTicker?symbol={product_code}'
        self.get_board_endpoint = 'api/v3/depth?symbol={product_code}'
        self.product_code = 'BTCUSDT'
        self.sell_endpoint = None
        self.client = binance_client(self.key, self.secret)

    def get_bid(self):
        """
        Method to get best bid on the Binance market.

        Returns:
            bid (float): Best bid on the Binance market
        """
        #print("binance call")
        response = self.get_ticker()
        bid = float(response['bidPrice'])
        return bid

    def get_ask(self):
        """
        Method to get best ask on the Binance market.

        Returns:
            ask (float): Best ask on the Binance market
        """
        response = self.get_ticker()
        ask = float(response['askPrice'])
        return ask

    def buy_market(self, quantity):
        self.client.order_market_buy(symbol="BTCUSDT", quantity=quantity)

    def sell_market(self, quantity):
        self.client.order_market_sell(symbol="BTCUSDT", quantity=quantity)


class Robinhood(Exchange):
    def __init__(self):
        self.totp = pyotp.TOTP("NBB2XJDL2IBBSYZG").now()
        r.login("Avbalsam", "Avrahamthegreat1@", mfa_code=self.totp)
    def get_bid(self):
        #print("rb call")
        return float(r.get_crypto_quote("BTC", "bid_price"))

    def get_ask(self):
        return float(r.get_crypto_quote("BTC", "ask_price"))


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


class Coinbase(Exchange):
    def __init__(self):
        self.key = "htOrL0BtSce3EJSk"
        self.secret = "hRtHO8WCWzFXS6enizoGGiPvJIEe2jem"
        self.client = coinbase_client(self.key, self.secret)

    def get_bid(self):
        return self.client.get_sell_price()

    def get_ask(self):
        return self.client.get_buy_price()

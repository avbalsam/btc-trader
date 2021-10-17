import logging
import os

from cryptoxlib.version_conversions import async_run
from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.bitforex import enums
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.bitforex.BitforexWebsocket import OrderBookSubscription, TradeSubscription, TickerSubscription, \
    Ticker24hSubscription
from cryptoxlib.version_conversions import async_run


class Bitforex:
    def __init__(self):
        LOG = logging.getLogger("cryptoxlib")
        LOG.setLevel(logging.INFO)
        LOG.addHandler(logging.StreamHandler())

        api_key = "5c93be0edb56bde9adde22997b87ceb6"
        sec_key = "cd0918f37fa80a73254d7189929d5d09"

        self.client = CryptoXLib.create_bitforex_client(api_key, sec_key)
        self.best_bid = float()
        self.best_ask = float()
        self.name = "Bitforex"

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            OrderBookSubscription(pair=Pair('BTC', 'USDT'), depth="0", callbacks=[self.order_book_update])
        ])

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        self.best_bid = response['data']['bids'][0]['price']
        self.best_ask = response['data']['asks'][0]['price']

    def get_bid(self):
        return float(self.best_bid)

    def get_ask(self):
        return float(self.best_ask)

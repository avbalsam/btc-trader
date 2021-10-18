import logging
import os
import uuid

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.hitbtc.HitbtcWebsocket import TickerSubscription, OrderbookSubscription, TradesSubscription, \
    AccountSubscription, ClientWebsocketHandle, CreateOrderMessage, CancelOrderMessage
from cryptoxlib.clients.hitbtc import enums
from cryptoxlib.version_conversions import async_run


class Hitbtc():
    def __init__(self):
        api_key = "uVMVK5NLUM-Ewb-tM3aYEsWK-L2pyrmX"
        sec_key = "ZOKzoTqZkyqvCnCOBBi3t2cD7mDqL7p_"

        self.client = CryptoXLib.create_hitbtc_client(api_key, sec_key)
        self.name = "Hitbtc"
        self.best_bid = float()
        self.best_ask = float()

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            OrderbookSubscription(pair=Pair("BTC", "USD"), callbacks=[self.order_book_update])
        ])

    def get_bid(self):
        return float(self.best_bid)

    def get_ask(self):
        return float(self.best_ask)

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            self.best_ask = response['params']['ask'][0]['price']
            self.best_bid = response['params']['bid'][0]['price']
        except KeyError:
            print(f"Callback order_book_update: [{response}]")
        except IndexError:
            pass

import logging
import os
import uuid

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.hitbtc.HitbtcWebsocket import TickerSubscription, OrderbookSubscription, TradesSubscription, \
    AccountSubscription, ClientWebsocketHandle, CreateOrderMessage, CancelOrderMessage
from cryptoxlib.clients.hitbtc import enums
from cryptoxlib.version_conversions import async_run

from exchange import Exchange


class Hitbtc(Exchange):
    def __init__(self):
        super().__init__()
        api_key = "uVMVK5NLUM-Ewb-tM3aYEsWK-L2pyrmX"
        sec_key = "ZOKzoTqZkyqvCnCOBBi3t2cD7mDqL7p_"

        self.client = CryptoXLib.create_hitbtc_client(api_key, sec_key)
        self.name = "Hitbtc"

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            TickerSubscription(pair=Pair("BTC", "USD"), callbacks=[self.order_book_update])
        ])

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            self.best_ask_by_symbol['BTC'] = response['params']['ask']
            self.best_bid_by_symbol['BTC'] = response['params']['bid']
        except KeyError:
            print(f"Callback order_book_update: [{response}]")

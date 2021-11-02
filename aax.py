import asyncio
import logging
import os

from binance import Binance
from bitforex import Bitforex

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.aax.AAXWebsocket import OrderBookSubscription, AccountSubscription
from cryptoxlib.version_conversions import async_run


class AAX:
    def __init__(self):
        self.name = "AAX"
        self.api_key = "a0dwBYAi3LcTRT0uPwV8VPsAz9"
        self.sec_key = "5d03a6614652887bb5835261be46a34d"
        user_id = "avbalsam@gmail.com"

        self.client = CryptoXLib.create_aax_client(self.api_key, self.sec_key)
        self.client.compose_subscriptions([
            OrderBookSubscription(pair=Pair('BTC', 'USDT'), depth=20, callbacks=[self.order_book_update]),
        ])

        self.best_bid = float()
        self.best_ask = float()

    def get_bid(self):
        return float(self.best_bid)

    def get_ask(self):
        return float(self.best_ask)

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            self.best_bid = response['bids'][0][0]
            self.best_ask = response['asks'][0][0]
        except KeyError:
            print(f"Out: [{response}]")
        except IndexError:
            pass
        except Exception:
            print("Uncaught exception in AAX")

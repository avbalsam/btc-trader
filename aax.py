import asyncio
import logging
import os

from binance import Binance
from bitforex import Bitforex

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.aax.AAXWebsocket import OrderBookSubscription, AccountSubscription
from cryptoxlib.version_conversions import async_run

from exchange import Exchange

class AAX(Exchange):
    def __init__(self, investor):
        super().__init__(investor)
        self.name = "AAX"
        self.api_key = "a0dwBYAi3LcTRT0uPwV8VPsAz9"
        self.sec_key = "5d03a6614652887bb5835261be46a34d"
        user_id = "avbalsam@gmail.com"

        self.client = CryptoXLib.create_aax_client(self.api_key, self.sec_key)
        self.client.compose_subscriptions([
            OrderBookSubscription(pair=Pair('BTC', 'USDT'), depth=20, callbacks=[self.order_book_update]),
        ])

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            self.best_bid_by_symbol['BTC'] = response['bids'][0][0]
            self.best_ask_by_symbol['BTC'] = response['asks'][0][0]
        except KeyError:
            print(f"Out: [{response}]")
        await self.invest()

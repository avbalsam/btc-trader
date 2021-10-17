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
        #LOG = logging.getLogger("cryptoxlib")
        #LOG.setLevel(logging.DEBUG)
        #LOG.addHandler(logging.StreamHandler())

        self.client = None
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

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        self.best_bid = response['bids'][0][0]
        self.best_ask = response['asks'][0][0]


async def main_loop(e):
    while True:
        print([i.get_bid() for i in e])
        await asyncio.sleep(1)

a = AAX()
b = Binance()
c = Bitforex()

async def run():
    while True:
        try:
            await asyncio.gather(*[a.client.start_websockets(), b.client.start_websockets(), c.client.start_websockets(), main_loop([a, b, c])])
            break
        except Exception as e:
            print(f"Out: {e}")
            continue
    try:
        await asyncio.gather(*[a.client.close(), b.client.close(), c.client.close()])
    except Exception as e:
        print(f"Out: {e}")
if __name__ == "__main__":
    async_run(run())

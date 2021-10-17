import logging
import os

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.aax.AAXWebsocket import OrderBookSubscription, AccountSubscription
from cryptoxlib.version_conversions import async_run


class AAX:
    def __init__(self):
        LOG = logging.getLogger("cryptoxlib")
        LOG.setLevel(logging.DEBUG)
        LOG.addHandler(logging.StreamHandler())

        self.client = None
        self.api_key = "a0dwBYAi3LcTRT0uPwV8VPsAz9"
        self.sec_key = "5d03a6614652887bb5835261be46a34d"
        user_id = "avbalsam@gmail.com"

        self.best_bid = float()
        self.best_ask = float()

        if __name__ == "__main__":
            async_run(self.run())

    def get_bid(self):
        return self.best_bid

    def get_ask(self):
        return self.best_ask

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        self.best_bid = response['bids'][0][0]
        self.best_ask = response['asks'][0][0]

    async def run(self):
        # to retrieve your API/SEC key go to your bitforex account, create the keys and store them in
        # BITFOREXAPIKEY/BITFOREXSECKEY environment variables
        self.client = CryptoXLib.create_aax_client(self.api_key, self.sec_key)

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            OrderBookSubscription(pair=Pair('BTC', 'USDT'), depth=20, callbacks=[self.order_book_update]),
        ])

        # Execute all websockets asynchronously
        await self.client.start_websockets()

        await self.client.close()


a = AAX()

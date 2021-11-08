from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.bitforex.BitforexWebsocket import OrderBookSubscription

from exchange import Exchange


class Bitforex(Exchange):
    def __init__(self, investor):
        super().__init__(investor)
        api_key = "5c93be0edb56bde9adde22997b87ceb6"
        sec_key = "cd0918f37fa80a73254d7189929d5d09"

        self.client = CryptoXLib.create_bitforex_client(api_key, sec_key)
        self.name = "Bitforex"

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            OrderBookSubscription(pair=Pair('BTC', 'USDT'), depth="0", callbacks=[self.order_book_update])
        ])

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            self.best_bid_by_symbol['BTC'] = response['data']['bids'][0]['price']
            self.best_ask_by_symbol['BTC'] = response['data']['asks'][0]['price']
        except KeyError:
            print(f"Out: [{response}]")
        await self.invest()

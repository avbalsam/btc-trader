import asyncio

from kucoin.client import Client
from kucoin.asyncio import KucoinSocketManager


class KuCoin:
    def __init__(self):
        global loop

        api_key = '617bad17b6ab210001dd3593'
        api_secret = '9ea8f4ba-0613-4561-8634-66f6b2428d3d'
        api_passphrase = 'Avrahamthegreat1@'

        self.client = Client(api_key, api_secret, api_passphrase)
        self.best_bid = float()
        self.best_ask = float()
        self.name = "KuCoin"

    async def start_websockets(self, loop):
        ksm = await KucoinSocketManager.create(loop, self.client, self.order_book_update)
        await ksm.subscribe('/market/ticker:BTC-USDT')

    async def order_book_update(self, msg):
        # print(f"Callback order book update: {msg}")
        if msg['topic'] == '/market/ticker:BTC-USDT':
            self.best_ask = msg['data']['bestAsk']
            self.best_bid = msg['data']['bestBid']

    def get_bid(self):
        return float(self.best_bid)

    def get_ask(self):
        return float(self.best_ask)

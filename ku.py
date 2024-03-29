from kucoin.client import Client
from kucoin.asyncio import KucoinSocketManager

from exchange import Exchange


class KuCoin(Exchange):
    def __init__(self, investor):
        super().__init__(investor)
        global loop

        api_key = '617bad17b6ab210001dd3593'
        api_secret = '9ea8f4ba-0613-4561-8634-66f6b2428d3d'
        api_passphrase = 'Avrahamthegreat1@'

        self.client = Client(api_key, api_secret, api_passphrase)
        self.name = "KuCoin"

    async def start_websockets(self, loop):
        ksm = await KucoinSocketManager.create(loop, self.client, self.order_book_update)
        await ksm.subscribe('/market/ticker:BTC-USDT')

    async def order_book_update(self, msg):
        # print(f"Callback order book update: {msg}")
        if '/market/ticker:' in msg['topic']:
            symbol = msg['topic'].replace("/market/ticker:", "", 1).replace("-USDT", "", 1)
            if symbol in self.best_ask_by_symbol and self.best_ask_by_symbol[symbol] == msg['data']['bestAsk']:
                return
            self.best_ask_by_symbol[symbol] = msg['data']['bestAsk']
            self.best_bid_by_symbol[symbol] = msg['data']['bestBid']
            await self.invest()

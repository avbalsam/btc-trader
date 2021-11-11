from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.hitbtc.HitbtcWebsocket import TickerSubscription

from exchange import Exchange


class Hitbtc(Exchange):
    def __init__(self, investor):
        super().__init__(investor)
        api_key = "uVMVK5NLUM-Ewb-tM3aYEsWK-L2pyrmX"
        sec_key = "ZOKzoTqZkyqvCnCOBBi3t2cD7mDqL7p_"

        self.client = CryptoXLib.create_hitbtc_client(api_key, sec_key)
        self.name = "Hitbtc"

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            TickerSubscription(pair=Pair(self.investor.get_symbol(), "USD"), callbacks=[self.order_book_update])
        ])

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def order_book_update(self, response: dict) -> None:
        # print(f"Callback order_book_update: [{response}]")
        try:
            symbol = response['params']['symbol'].replace("USD", "", 1)
            if symbol in self.best_ask_by_symbol and self.best_ask_by_symbol[symbol] == response['params']['ask']:
                return
            self.best_ask_by_symbol[symbol] = response['params']['ask']
            self.best_bid_by_symbol[symbol] = response['params']['bid']
            await self.invest()
        except KeyError:
            print(f"HitBtc out: [{response}]")

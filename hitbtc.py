import asyncio

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.hitbtc.HitbtcWebsocket import TickerSubscription

from exchange import Exchange


class Hitbtc(Exchange):
    def __init__(self, symbols_to_trade: list, update_event: asyncio.Event):
        super().__init__()
        self.update_event = update_event
        api_key = "uVMVK5NLUM-Ewb-tM3aYEsWK-L2pyrmX"
        sec_key = "ZOKzoTqZkyqvCnCOBBi3t2cD7mDqL7p_"

        self.client = CryptoXLib.create_hitbtc_client(api_key, sec_key)
        self.name = "Hitbtc"

        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            TickerSubscription(pair=Pair(symbol, "USD"), callbacks=[self.order_book_update])
            for symbol in symbols_to_trade
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
            self.update_event.set()
        except KeyError:
            print(f"HitBtc out: [{response}]")

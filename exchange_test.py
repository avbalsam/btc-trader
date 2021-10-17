import logging
import os
from datetime import datetime

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.binance.BinanceWebsocket import AccountSubscription, OrderBookTickerSubscription, \
    TradeSubscription, OrderBookSymbolTickerSubscription, CandlestickSubscription
from cryptoxlib.clients.binance.enums import Interval
from cryptoxlib.Pair import Pair
from cryptoxlib.version_conversions import async_run


class Binance:
    def __init__(self):
        LOG = logging.getLogger("cryptoxlib")
        LOG.setLevel(logging.DEBUG)
        LOG.addHandler(logging.StreamHandler())
        self.name = "Binance"
        self.best_bid = float()
        self.best_ask = float()
        self.stream_error = False

        self.api_key = "mf47OdnGELNlVentiyRGQOmKvl7HjpXn7zLPwA5xnOWSM5Dv3kCAwk4II81oQfLP"
        self.sec_key = "ABiqm9CQRV2tF9dQOaplFv8esOfqYFHyVDVjDVLK3AYvMk1qpNoSYy0mN8tMwR3f"

        self.client = CryptoXLib.create_binance_testnet_client(self.api_key, self.sec_key)

        if __name__ == "__main__":
            async_run(self.run())

    async def account_update(self, response: dict) -> None:
        print(f"Callback account_update: [{response}]")

    async def orderbook_ticker_update(self, response: dict) -> None:
        print(f"Callback orderbook_ticker_update: [{response}]")
        self.best_ask = response['data']['a']
        self.best_bid = response['data']['b']

    async def run(self):
        # Bundle several subscriptions into a single websocket
        self.client.compose_subscriptions([
            OrderBookSymbolTickerSubscription(pair=Pair("BTC", "USDT"), callbacks=[self.orderbook_ticker_update])
        ])

        # Bundle another subscriptions into a separate websocket
        self.client.compose_subscriptions([
            AccountSubscription(callbacks=[self.account_update])
        ])

        # Execute all websockets asynchronously
        await self.client.start_websockets()

        await self.client.close()



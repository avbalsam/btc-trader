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
        self.name = "Binance"
        self.best_bid = float()
        self.best_ask = float()

        self.api_key = "mf47OdnGELNlVentiyRGQOmKvl7HjpXn7zLPwA5xnOWSM5Dv3kCAwk4II81oQfLP"
        self.sec_key = "ABiqm9CQRV2tF9dQOaplFv8esOfqYFHyVDVjDVLK3AYvMk1qpNoSYy0mN8tMwR3f"

        self.client = CryptoXLib.create_binance_testnet_client(self.api_key, self.sec_key)

        self.client.compose_subscriptions([
            OrderBookSymbolTickerSubscription(pair=Pair("BTC", "USDT"), callbacks=[self.orderbook_ticker_update])
        ])

        self.client.compose_subscriptions([
            AccountSubscription(callbacks=[self.account_update])
        ])

    def get_bid(self):
        return float(self.best_bid)

    def get_ask(self):
        return float(self.get_ask())

    async def account_update(self, response: dict) -> None:
        print(f"Callback account_update: [{response}]")

    async def orderbook_ticker_update(self, response: dict) -> None:
        # print(f"Callback orderbook_ticker_update: [{response}]")
        try:
            self.best_ask = response['data']['a']
            self.best_bid = response['data']['b']
        except KeyError:
            print(f"Out: [{response}]")
        except IndexError:
            pass
        except Exception:
            print("Uncaught exception in Binance")

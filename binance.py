import logging
import os
from datetime import datetime

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.binance import enums
from cryptoxlib.clients.binance.BinanceWebsocket import AccountSubscription, OrderBookTickerSubscription, \
    TradeSubscription, OrderBookSymbolTickerSubscription, CandlestickSubscription
from cryptoxlib.clients.binance.enums import Interval, TimeInForce
from cryptoxlib.Pair import Pair
from cryptoxlib.version_conversions import async_run


class Binance:
    def __init__(self, testnet=True):
        self.name = "Binance"
        self.best_bid = float()
        self.best_ask = float()
        self.mean_diff = list()
        self.holdings = {'btc': 0, 'usdt': 0}
        self.commission = .00075

        self.api_key = "mf47OdnGELNlVentiyRGQOmKvl7HjpXn7zLPwA5xnOWSM5Dv3kCAwk4II81oQfLP"
        self.sec_key = "ABiqm9CQRV2tF9dQOaplFv8esOfqYFHyVDVjDVLK3AYvMk1qpNoSYy0mN8tMwR3f"

        self.api_key_testnet = "VCEnHDaubZwJkv7H61ivIoa2yBrFBJKc9UOR6bLx2ciTQHH75NcNrLuCpwjdDH0B"
        self.sec_key_testnet = "9XlcXTFRSYJG6LrRMt8nzjZJsfz0g6C6XpYNSHuKoEvoot6qybNXuaM7jyGcZ5Ge"

        if testnet is True:
            self.client = CryptoXLib.create_binance_testnet_client(self.api_key_testnet, self.sec_key_testnet)
        else:
            self.client = CryptoXLib.create_binance_client(self.api_key, self.sec_key)

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

    async def buy_market(self):
        usdt_amt = float(self.holdings['usdt'])
        btc_value = round((usdt_amt - usdt_amt * self.commission) / float(self.best_ask), 5)
        print(btc_value)
        await self.client.create_order(Pair("BTC", "USDT"), side=enums.OrderSide.BUY, type=enums.OrderType.MARKET,
                                       quantity="0.1", time_in_force=TimeInForce.IMMEDIATE_OR_CANCELLED,
                                       new_order_response_type=enums.OrderResponseType.FULL)
        await self.update_account_balances()

    async def sell_market(self):
        btc_amt = float(self.holdings['btc'])
        await self.client.create_order(Pair("BTC", "USDT"), side=enums.OrderSide.SELL, type=enums.OrderType.MARKET,
                                       quantity=str(round(btc_amt, 5)-.00001), time_in_force=TimeInForce.IMMEDIATE_OR_CANCELLED,
                                       new_order_response_type=enums.OrderResponseType.FULL)
        await self.update_account_balances()

    async def update_account_balances(self):
        account = await self.client.get_account(5000)
        btc = float(account['response']['balances'][1]['free'])
        usdt = float(account['response']['balances'][6]['free'])
        self.holdings = {'btc': btc, 'usdt': usdt}
        print(self.holdings)

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

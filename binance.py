import asyncio
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

from exchange import Exchange

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


class Binance(Exchange):
    def __init__(self, testnet=True):
        super().__init__()
        self.name = "Binance"
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

    async def account_update(self, response: dict) -> None:
        print(f"Callback account_update: [{response}]")
        if response['data']['e'] == 'outboundAccountPosition':
            assets = response['data']
            for asset in assets:
                print(asset)

    async def buy_market(self, symbol: str) -> None:
        """Buys 0.0014 bitcoin at market price"""
        usdt_amt = float(self.holdings['usdt'])
        btc_value = round((usdt_amt - usdt_amt * self.commission) / self.get_ask(symbol), 5)
        buy_price = str(truncate(self.get_ask(symbol), 5))
        print(f"Buying .0014 bitcoin for {buy_price} per bitcoin. Btc value of current USDT balance: {btc_value}")
        if btc_value > 0.0014:
            await self.client.create_order(Pair("BTC", "USDT"), side=enums.OrderSide.BUY, type=enums.OrderType.LIMIT,
                                           quantity="0.0014", price=buy_price,
                                           time_in_force=TimeInForce.IMMEDIATE_OR_CANCELLED,
                                           new_order_response_type=enums.OrderResponseType.FULL)
        else:
            print("Insufficient account balance to perform trade")
        await self.update_account_balances()

    async def sell_market(self, symbol: str) -> None:
        """Attempts to sell all bitcoin at market price"""
        btc_amt = float(self.holdings['btc'])
        sell_price = str(truncate(self.get_bid(symbol), 5))
        sell_amt = str(truncate(btc_amt, 4))
        print(f"Selling {sell_amt} bitcoins for {sell_price} per bitcoin. Total amount sold: {sell_amt}")
        try:
            await self.client.create_order(Pair("BTC", "USDT"), side=enums.OrderSide.SELL, type=enums.OrderType.LIMIT,
                                           quantity=sell_amt, price=sell_price,
                                           time_in_force=TimeInForce.IMMEDIATE_OR_CANCELLED,
                                           new_order_response_type=enums.OrderResponseType.FULL)
        except Exception as e:
            print(f"Out: {e}")
        await self.update_account_balances()

    async def update_account_balances(self) -> None:
        """Updates self.holdings based on balances in client account"""
        account = await self.client.get_account(5000)
        assets = account['response']['balances']
        btc = 0.0
        usdt = 0.0
        for a in range(0, len(assets)):
            if assets[a]['asset'] == 'BTC':
                btc = float(assets[a]['free'])
            if assets[a]['asset'] == 'USDT':
                usdt = float(assets[a]['free'])
        self.holdings = {'btc': btc, 'usdt': usdt}
        print(self.holdings)

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def orderbook_ticker_update(self, response: dict) -> None:
        # print(f"Callback orderbook_ticker_update: [{response}]")
        try:
            self.best_ask_by_symbol['BTC'] = response['data']['a']
            self.best_bid_by_symbol['BTC'] = response['data']['b']
        except KeyError:
            print(f"Out: [{response}]")
        except IndexError:
            pass
        except Exception:
            print("Uncaught exception in Binance")

    async def get_account_trades(self, symbol: Pair) -> list:
        """Gets all account trades in nicely formatted dictionary

        Args:
            symbol (Pair): Pair object representing symbol pair to get trades of

        Returns:
            trades_formatted (dict): Nicely formatted dictionary containing important information about account trades"""
        from_id = 0
        all_trades = list()
        while True:
            trades_from_id = await self.client.get_account_trades(pair=symbol, limit=1000, from_id=from_id)
            trades_from_id = trades_from_id['response']
            trades_formatted_from_id = list()
            for trade in trades_from_id:
                id = trade['id']
                side = 'buy' if trade['isBuyer'] is True else 'sell'
                price = float(trade['price'])
                qty = float(trade['qty'])
                quote_qty = float(trade['quoteQty'])
                commission = float(trade['commission'])
                t = {"id": id, "side": side, "price": price, "quantity": qty, "quote_qty": quote_qty,
                     "commission": commission}
                trades_formatted_from_id.append(t)
            if len(trades_formatted_from_id) == 0:
                return all_trades
            else:
                for trade in trades_formatted_from_id:
                    all_trades.append(trade)
                from_id = trades_formatted_from_id[-1]['id'] + 1

    async def print_trades(self, symbol: Pair) -> None:
        """Prints all trades made by account

        Args:
            symbol (Pair): Pair object representing symbol pair to get trades of"""
        trades = await self.get_account_trades(symbol)
        for trade in trades:
            print(trade)
        print(len(trades))

    async def get_profit(self, symbol: Pair, commission=0.00075) -> float:
        """Returns total profit taking commission into account. This may take time if best_bid
        has not been generated yet.

        Args:
            symbol (Pair): Symbol pair to calculate profit for.
            commission (float): commission charged on given transactions.

        Returns:
            total_profit (float): Profit gained during recorded account transactions
        """
        usdt_bal = float()
        btc_bal = float()
        total_usdt_traded = float()
        trades = await self.get_account_trades(symbol)
        for trade in trades:
            total_usdt_traded += trade['quote_qty']
            fees = trade['quote_qty'] * commission
            if trade['side'] == 'buy':
                btc_bal += trade['quantity']
                usdt_bal -= trade['quote_qty']
                usdt_bal -= fees
            if trade['side'] == 'sell':
                usdt_bal += trade['quote_qty']
                usdt_bal -= fees
                btc_bal -= trade['quantity']
        while self.get_bid() == 0.0:
            print("no bid...")
            await asyncio.sleep(1)
        total_profit = usdt_bal + btc_bal * self.get_bid()
        return total_profit

    async def get_volume(self, symbol: Pair) -> float:
        total_usdt_traded = float()
        trades = await self.get_account_trades(symbol)
        for trade in trades:
            total_usdt_traded += trade['quote_qty']
        return total_usdt_traded

import asyncio
import logging
from datetime import datetime

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.binance import enums
from cryptoxlib.clients.binance.BinanceWebsocket import AccountSubscription, OrderBookTickerSubscription, \
    TradeSubscription, OrderBookSymbolTickerSubscription, CandlestickSubscription, DepthSubscription
from cryptoxlib.clients.binance.enums import Interval, TimeInForce
from cryptoxlib.Pair import Pair
from cryptoxlib.version_conversions import async_run

from exchange import Exchange


def truncate(n: float, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


class Binance(Exchange):
    def __init__(self, investor, testnet=True):
        super().__init__(investor)
        self.name = "Binance"
        self.holdings = {'BTC': 0, 'USDT': 0}
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
            DepthSubscription(pair=Pair(self.investor.get_symbol(), "USDT"), callbacks=[self.orderbook_ticker_update])
        ])

        self.client.compose_subscriptions([
            AccountSubscription(callbacks=[self.account_update])
        ])

    async def account_update(self, response: dict) -> None:
        if response['data']['e'] == 'outboundAccountPosition':
            assets = response['data']['B']
            for asset in assets:
                symbol = asset['a']
                quantity = asset['f']
                self.holdings[symbol] = float(quantity)
            print(f"Callback account update: {assets}")

    async def update_account_balances(self) -> None:
        """Updates self.holdings based on balances in client account"""
        tries = 0
        while True:
            try:
                account = await self.client.get_account(5000)
                break
            except Exception as e:
                tries += 1
                print(f"Unable to get account data. {e}. Trying again...\nTotal tries so far: {tries}")
        assets = account['response']['balances']
        for a in range(0, len(assets)):
            symbol = assets[a]['asset']
            quantity = assets[a]['free']
            self.holdings[symbol] = float(quantity)

    async def start_websockets(self, loop) -> None:
        await self.client.start_websockets()

    async def orderbook_ticker_update(self, response: dict) -> None:
        # print(f"Callback orderbook_ticker_update: [{response}]")
        try:
            symbol = response['data']['s'].replace("USDT", "", 1)
            if symbol in self.best_ask_by_symbol and self.best_ask_by_symbol[symbol] == response['data']['a']:
                return
            orderbook_bids = response['data']['b']
            orderbook_asks = response['data']['a']
            # Look for best bid and ask whose quantity is not zero
            for bid in orderbook_bids:
                if float(bid[1]) != 0.0:
                    self.best_bid_by_symbol[symbol] = float(bid[0])
                    break
            for ask in orderbook_asks:
                if float(ask[1]) != 0.0:
                    self.best_ask_by_symbol[symbol] = float(ask[0])
                    break
        except KeyError:
            print(f"Out: [{response}]")

    async def get_account_trades(self, symbol: str) -> list:
        """Gets all account trades in nicely formatted dictionary

        Args:
            symbol (str): String representing symbol pair to get trades of

        Returns:
            trades_formatted (dict): Nicely formatted dictionary containing important information about account trades"""
        from_id = 0
        all_trades = list()
        while True:
            trades_from_id = await self.client.get_account_trades(pair=Pair(symbol, 'USDT'), limit=1000,
                                                                  from_id=from_id)
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

    async def print_trades(self, symbol: str) -> None:
        """Prints all trades made by account

        Args:
            symbol (str): String representing symbol pair to get trades of"""
        trades = await self.get_account_trades(symbol)
        for trade in trades:
            print(trade)
        print(len(trades))

    async def get_profit(self, symbol: str, commission=0.00075) -> float:
        """Returns total profit taking commission into account. This may take time if best_bid
        has not been generated yet.

        Args:
            symbol (str): Symbol pair to calculate profit for.
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
        while self.get_bid(symbol) == 0.0:
            print("no bid...")
            await asyncio.sleep(1)
        total_profit = usdt_bal + btc_bal * self.get_bid(symbol)
        return total_profit

    async def get_volume(self, symbol: str) -> float:
        total_usdt_traded = float()
        trades = await self.get_account_trades(symbol)
        for trade in trades:
            total_usdt_traded += trade['quote_qty']
        return total_usdt_traded

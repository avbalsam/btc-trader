import asyncio
import csv
import shutil
import threading
import time
import numpy as np
import logging
import os

from binance import Binance
from aax import AAX
from hitbtc import Hitbtc
from ku import KuCoin


def read_csv(filename):
    """
    Reads .csv file to list.

    Args:
        filename (str): Include .csv extension
    Returns:
        data (list): Nested list, with headers in first row
    """
    with open(f"./outputs/{filename}", "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        data = [x for x in data if x != []]
    return data


def write_to_csv(filename, fields, data):
    """
    Writes input data to csv file.

    Args:
        filename (str): Do not include .csv extension.
        fields (list): First row of table.
        data (list): Nested list. Each element represents one column of csv file (in this case, one exchange).
    """
    if not (os.path.exists("./web/outputs")):
        os.mkdir("./web/outputs")
    data = np.array(data).T.tolist()
    try:
        if os.path.exists(f"./web/outputs/{filename}.csv"):
            with open(f"./web/outputs/{filename}.csv", "a", newline='') as f:
                write = csv.writer(f)
                write.writerows(data)
        else:
            with open(f"./web/outputs/{filename}.csv", "w", newline='') as f:
                write = csv.writer(f)
                write.writerow(fields)
                write.writerows(data)
    except PermissionError:
        print("Unable to gain access to file. Please close any programs which are using " + filename + ".csv...")


# LOG = logging.getLogger("cryptoxlib")
# LOG.setLevel(logging.INFO)
# LOG.addHandler(logging.StreamHandler())


class Investor:
    def __init__(self, symbol: str, calibration_time: int, timestep: float, buy_disc: float, verbose_logging=False, testnet=False):
        """Initializes an instance of Investor class

        Args:
            symbol (str): String representing symbol this Investor will trade
            calibration_time (int): Amount of time Investor should calculate market data before investing, in seconds
            timestep (float): Amount of time in between market data calculations, in seconds.
            verbose_logging (bool): Determines whether the investor will log verbose information.
            testnet (bool): Determines whether to use real money or not.
            buy_disc (float): Required discrepancy to buy as a percentage of current symbol value (in decimal form)
        """
        self.symbol = symbol
        self.calibration_loops = round(calibration_time / timestep)
        self.buy_disc = buy_disc
        self.verbose_logging = verbose_logging
        self.exchange_list = [Binance(self, testnet=testnet), AAX(self), Hitbtc(self), KuCoin(self)]

        self.sell_order_active = False
        self.buy_order_active = False
        self.latest_buy_order = None
        self.active_sell_orders = list()
        self.historical_bids = [[e.get_bid(symbol)] for e in self.exchange_list]
        self.fields = [e.name for e in self.exchange_list]
        self.diff_lists = [[e.get_bid(symbol) - self.exchange_list[0].get_bid(symbol)] for e in self.exchange_list]
        self.avg_diff = [e.get_bid(symbol) - self.exchange_list[0].get_bid(symbol) for e in self.exchange_list]
        self.loops_completed = 0
        self.invest_checks_completed = 0

    def get_symbol(self):
        return self.symbol

    async def get_market_data(self):
        # print(await self.exchange_list[0].get_profit('BTC', commission=.00075))
        # print(await self.exchange_list[0].print_trades('BTC'))
        # print(await self.exchange_list[0].get_volume('BTC'))
        await self.exchange_list[0].update_account_balances()
        self.loops_completed = 0
        while True:
            self.loops_completed += 1
            await asyncio.sleep(1)
            bids = [e.get_bid(self.symbol) for e in self.exchange_list]
            if 0.0 in bids:
                self.loops_completed -= 1
                await asyncio.sleep(1)
                print(bids)
                continue
            if self.verbose_logging:
                print(f"{self.symbol}: {time.ctime()} {bids} {self.loops_completed}")
            if self.loops_completed % 30 == 0:
                if self.loops_completed > self.calibration_loops:
                    self.historical_bids = self.historical_bids[-self.calibration_loops:]
                    self.diff_lists = self.diff_lists[-self.calibration_loops:]
                print(f"\n{self.symbol}: Current time: {time.ctime()}\n"
                      f"{self.loops_completed} data collection loops completed. "
                      f"{self.invest_checks_completed} invest checks completed...\n"
                      f"Bids: {bids}\n"
                      f"Avg diff: {self.avg_diff}\n"
                      f"Current holdings. {self.symbol}: {self.exchange_list[0].holdings[self.symbol]}, "
                      f"USDT: {self.exchange_list[0].holdings['USDT']}\n")
                write_to_csv(f'bid_data_{self.symbol}', self.fields, [bids[-30:] for bids in self.historical_bids])
                write_to_csv(f'diffs_data_{self.symbol}', self.fields, [diffs[-30:] for diffs in self.diff_lists])
                if self.loops_completed % 480 == 0:
                    await self.exchange_list[0].update_account_balances()
                    if self.loops_completed % self.calibration_loops == 0:
                        self.historical_bids = self.historical_bids[-self.calibration_loops:]
                        self.diff_lists = self.diff_lists[-self.calibration_loops:]

            for e in range(0, len(self.exchange_list)):
                self.historical_bids[e].append(self.exchange_list[e].get_bid(self.symbol))
                self.diff_lists[e].append(self.exchange_list[e].get_bid(self.symbol) - self.exchange_list[0].get_bid(self.symbol))
                if self.loops_completed <= self.calibration_loops:
                    self.avg_diff[e] = self.avg_diff[e] * ((self.loops_completed - 1) / self.loops_completed) + \
                                       self.diff_lists[e][-1] / self.loops_completed
                else:
                    self.avg_diff[e] = np.mean(self.diff_lists[e][-self.calibration_loops:])

    async def invest(self):
        if self.buy_order_active or len(self.active_sell_orders) > 0:
            return
        self.invest_checks_completed += 1
        buy_disc_count = 0
        sell_disc_count = 0
        disc_list = [self.exchange_list[e].get_ask(self.symbol) - self.exchange_list[0].get_ask(self.symbol) -
                     self.avg_diff[e] for e in range(0, len(self.exchange_list))]
        for d in disc_list:
            if d > self.exchange_list[0].get_ask(self.symbol) * self.buy_disc:
                buy_disc_count += 1
            elif d < 0:
                sell_disc_count += 1
        if self.verbose_logging:
            print(f"{self.symbol}: {[round(d, 2) for d in disc_list]} {self.invest_checks_completed}")
        if self.loops_completed > self.calibration_loops:
            if buy_disc_count >= len(self.exchange_list) - 1 and self.exchange_list[0].holdings['USDT'] > 50:
                order_id = await self.exchange_list[0].buy_market(self.symbol)
                if order_id is not None:
                    self.latest_buy_order = order_id
                    self.buy_order_active = True
                await asyncio.sleep(.2)
                if self.buy_order_active:
                    try:
                        await self.exchange_list[0].cancel_order(self.symbol, self.latest_buy_order)
                    except Exception as e:
                        print(f"{self.symbol} unable to cancel buy order: {e}")
                    self.buy_order_active = False
        if sell_disc_count >= len(self.exchange_list) - 2:
            order_id = await self.exchange_list[0].sell_market(self.symbol)
            if order_id is not None:
                self.active_sell_orders.append(order_id)

    async def cancel_orders(self):
        orders_to_cancel = list()
        while True:
            if self.verbose_logging:
                print(f"{self.symbol} active orders: {self.active_sell_orders}")
            if self.active_sell_orders != orders_to_cancel:
                orders_to_cancel = self.active_sell_orders
            await asyncio.sleep(10)
            for order in orders_to_cancel:
                try:
                    await self.exchange_list[0].cancel_order(self.symbol, int(order))
                    print(f"{self.symbol} order cancelled. Order ID: {order}")
                except Exception as e:
                    print(f"Unable to cancel sell order: {e}")
                self.active_sell_orders.remove(order)


async def start_websockets(exchange, loop):
    while True:
        try:
            await exchange.start_websockets(loop)
        except Exception as e:
            print(f"{exchange.name} errored out: {e}. Restarting websocket...")


if __name__ == "__main__":
    try:
        shutil.rmtree("./web/outputs/")
    except FileNotFoundError:
        pass
    os.mkdir("./web/outputs")
    symbols_to_trade = ["BTC", "ETH"]
    investors = list()
    for symbol in symbols_to_trade:
        investors.append(Investor(symbol=symbol,
                                  calibration_time=10000,
                                  timestep=0.5, buy_disc=0.0013,
                                  verbose_logging=True, testnet=False))
    loop = asyncio.get_event_loop()
    coros = list()
    for investor in investors:
        coros.append(asyncio.gather(*[start_websockets(e, loop) for e in investor.exchange_list],
                                 investor.get_market_data(), investor.cancel_orders()))
    results = asyncio.gather(*coros)
    loop.run_until_complete(results)
    loop.close()

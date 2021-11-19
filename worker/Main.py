import asyncio
import csv
import shutil
import threading
import time
import logging
import os

from binance import Binance
from aax import AAX
from hitbtc import Hitbtc
from ku import KuCoin

import csv

import matplotlib.pyplot as plt
from flask import Flask, Response

import os
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import numpy as np


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
    data = np.array(data).T.tolist()
    try:
        if os.path.exists(f"./outputs/{filename}.csv"):
            with open(f"./outputs/{filename}.csv", "a", newline='') as f:
                write = csv.writer(f)
                write.writerows(data)
        else:
            with open(f"./outputs/{filename}.csv", "w", newline='') as f:
                write = csv.writer(f)
                write.writerow(fields)
                write.writerows(data)
    except PermissionError:
        print("Unable to gain access to file. Please close any programs which are using " + filename + ".csv...")


# LOG = logging.getLogger("cryptoxlib")
# LOG.setLevel(logging.INFO)
# LOG.addHandler(logging.StreamHandler())


class Investor:
    def __init__(self, symbol: str, calibration_time: int, timestep: float, buy_disc: float, sell_disc: float,
                 verbose_logging=False, testnet=False):
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
        self.sell_disc = sell_disc
        self.verbose_logging = verbose_logging
        self.exchange_list = [Binance(self, testnet=testnet), AAX(self), Hitbtc(self), KuCoin(self)]

        self.bids = list()
        self.asks = list()
        self.current_diff = list()
        self.avg_diff = [e.get_bid(symbol) - self.exchange_list[0].get_ask(symbol) for e in self.exchange_list]

        self.disc_list = list()
        self.sell_order_active = False
        self.buy_order_active = False
        self.latest_buy_order = None
        self.active_sell_orders = list()
        self.active_buy_orders = list()
        self.loops_completed = 0
        self.invest_checks_completed = 0

    def get_symbol(self):
        return self.symbol

    def get_current_disc(self):
        return self.disc_list

    async def get_market_data(self):
        # print(await self.exchange_list[0].get_profit('BTC', commission=.00075))
        # print(await self.exchange_list[0].print_trades('BTC'))
        # print(await self.exchange_list[0].get_volume('BTC'))
        await self.exchange_list[0].update_account_balances()
        self.loops_completed = 0
        while True:
            self.loops_completed += 1
            await asyncio.sleep(1)
            self.bids = [e.get_bid(self.symbol) for e in self.exchange_list]
            self.asks = [e.get_ask(self.symbol) for e in self.exchange_list]
            self.current_diff = [e.get_bid(self.symbol) - self.exchange_list[0].get_ask(self.symbol)
                                 for e in self.exchange_list]
            self.avg_diff = [self.avg_diff[e] * ((self.loops_completed - 1) / self.loops_completed) \
                             + self.current_diff[e] / self.loops_completed for e in range(0, len(self.exchange_list))]
            self.disc_list = [self.current_diff[e] - self.avg_diff[e] for e in range(0, len(self.exchange_list))]
            if 0.0 in self.bids:
                self.loops_completed -= 1
                await asyncio.sleep(1)
                print(self.bids)
                continue
            if self.verbose_logging:
                print(f"{self.symbol}: {time.ctime()} {self.bids} {self.loops_completed}")
            if self.loops_completed % 60 == 0:
                print(f"\n{self.symbol}: Current time: {time.ctime()}\n"
                      f"{self.loops_completed} data collection loops completed. "
                      f"{self.invest_checks_completed} invest checks completed...\n"
                      f"Bids: {self.bids}\n"
                      f"Current holdings. {self.symbol}: {self.exchange_list[0].holdings[self.symbol]}, "
                      f"USDT: {self.exchange_list[0].holdings['USDT']}\n")
                await self.exchange_list[0].update_account_balances()
            await self.invest()

    async def invest(self):
        if self.buy_order_active or len(self.active_sell_orders) > 0:
            return
        self.invest_checks_completed += 1
        buy_disc_count = 0
        sell_disc_count = 0
        for d in self.disc_list:
            if d > self.exchange_list[0].get_ask(self.symbol) * self.buy_disc:
                buy_disc_count += 1
            elif d < self.exchange_list[0].get_bid(self.symbol) * self.sell_disc:
                sell_disc_count += 1
        if self.verbose_logging:
            print(f"{self.symbol}: {[round(d, 2) for d in self.disc_list]} {self.invest_checks_completed}")
        if self.loops_completed > self.calibration_loops and buy_disc_count >= len(self.exchange_list) - 1 \
                and self.exchange_list[0].holdings['USDT'] > 10:
            order_id = await self.exchange_list[0].buy_market(self.symbol)
            if order_id is not None:
                self.latest_buy_order = order_id
                self.buy_order_active = True
            await asyncio.sleep(.3)
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

    async def cancel_sell_orders(self):
        orders_to_cancel = list()
        while True:
            if self.verbose_logging and len(self.active_sell_orders) > 0:
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
    symbols_to_trade = ["BTC", "ETH"]
    investors = dict()
    loop = asyncio.get_event_loop()
    coros = list()
    for symbol in symbols_to_trade:
        investors[symbol] = Investor(symbol=symbol,
                                     calibration_time=10000,
                                     timestep=0.5, buy_disc=0.00015, sell_disc=0,
                                     verbose_logging=False, testnet=False)
        coros.append(asyncio.gather(*[start_websockets(e, loop) for e in investors[symbol].exchange_list],
                                    investors[symbol].get_market_data(), investors[symbol].cancel_sell_orders()))
    results = asyncio.gather(*coros)
    loop.run_until_complete(results)
    loop.close()

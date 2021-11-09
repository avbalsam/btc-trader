import asyncio
import csv
import time
import numpy as np
import logging

from binance import Binance
from aax import AAX
from hitbtc import Hitbtc
from ku import KuCoin


def read_csv(filename):
    """
    Reads .csv file to list.

    Args:
        filename (str): Do not include .csv extension
    Returns:
        data (list): Nested list, with headers in first row
    """
    with open("data/" + filename + ".csv", "r") as f:
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
        data (list): Nested list. Each element represents one row.
    """
    try:
        with open(f"{filename}.csv", "w") as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(data)
    except PermissionError:
        print("Unable to gain access to file. Please close any programs which are using " + filename + ".csv...")


# LOG = logging.getLogger("cryptoxlib")
# LOG.setLevel(logging.INFO)
# LOG.addHandler(logging.StreamHandler())


class Investor:
    def __init__(self, symbol: str, calibration_time: int, timestep: float):
        """Initializes an instance of Investor class

        Args:
            symbol (str): String representing symbol this Investor will trade
            calibration_time (int): Amount of time Investor should calculate market data before investing, in seconds
            timestep (float): Amount of time in between market data calculations, in seconds.
        """
        self.calibration_loops = round(calibration_time / timestep)
        self.exchange_list = [Binance(self, testnet=False), AAX(self), Hitbtc(self), KuCoin(self)]
        self.symbol = symbol
        self.historical_bids = [list() for i in range(0, len(self.exchange_list))]
        self.fields = [exchange.name for exchange in self.exchange_list]
        self.diff_lists = [list() for i in range(0, len(self.exchange_list))]
        self.avg_diff = [e.get_bid(symbol) - self.exchange_list[0].get_bid(symbol) for e in self.exchange_list]
        self.loops_completed = 0
        self.invest_checks_completed = 0
        self.order_active = False

    async def get_market_data(self):
        # print(await self.exchange_list[0].get_profit('BTC', commission=.00075))
        # print(await self.exchange_list[0].print_trades('BTC'))
        # print(await self.exchange_list[0].get_volume('BTC'))
        # return
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
            print(f"{time.ctime()} {bids} {self.loops_completed}")
            if self.loops_completed % 30 == 0:
                if self.loops_completed > self.calibration_loops:
                    self.historical_bids = self.historical_bids[-self.calibration_loops:]
                    self.diff_lists = self.diff_lists[-self.calibration_loops:]
                print(f"\nCurrent time: {time.ctime()}\n"
                      f"{self.loops_completed} data collection loops completed. "
                      f"{self.invest_checks_completed} invest checks completed...\n"
                      f"Bids: {bids}\n"
                      f"Avg diff: {self.avg_diff}\n"
                      f"Current holdings. BTC: {self.exchange_list[0].holdings['BTC']}, "
                      f"USDT: {self.exchange_list[0].holdings['USDT']}\n")
                if self.loops_completed % 480 == 0:
                    await self.exchange_list[0].update_account_balances()
                    write_to_csv('bid_data', self.fields, self.historical_bids)
                    write_to_csv('diffs_data', self.fields, self.diff_lists)
            for e in range(0, len(self.exchange_list)):
                self.historical_bids[e].append(self.exchange_list[e].get_bid(self.symbol))
                self.diff_lists[e].append(self.exchange_list[e].get_bid(self.symbol) - self.exchange_list[0].get_bid(self.symbol))
                if self.loops_completed <= self.calibration_loops:
                    self.avg_diff[e] = self.avg_diff[e] * ((self.loops_completed - 1) / self.loops_completed) + \
                                       self.diff_lists[e][-1] / self.loops_completed
                else:
                    self.avg_diff[e] = np.mean(self.diff_lists[e][-self.calibration_loops:])

    async def invest(self):
        if self.order_active:
            return
        self.invest_checks_completed += 1
        buy_disc_count = 0
        sell_disc_count = 0
        disc_list = [self.exchange_list[e].get_bid(self.symbol) - self.exchange_list[0].get_bid(self.symbol) -
                     self.avg_diff[e] for e in range(0, len(self.exchange_list))]
        for d in disc_list:
            if d > 65:
                buy_disc_count += 1
            elif d < 0:
                sell_disc_count += 1
        # print(f"{[round(d, 2) for d in disc_list]} {self.invest_checks_completed}")
        if self.loops_completed > self.calibration_loops:
            if buy_disc_count >= len(self.exchange_list) - 1 and self.exchange_list[0].holdings['USDT'] > 0:
                self.order_active = True
                await self.exchange_list[0].buy_market(self.symbol)
                self.order_active = False
                self.order_active = False
        if sell_disc_count >= len(self.exchange_list) - 1:
            self.order_active = True
            await self.exchange_list[0].sell_market(self.symbol)
            self.order_active = False
            self.order_active = False


async def start_websockets(exchange, loop):
    while True:
        try:
            await exchange.start_websockets(loop)
        except Exception as e:
            print(f"{exchange.name} errored out: {e}. Restarting websocket...")


if __name__ == "__main__":
    investor = Investor("BTC", 5000, 1)
    loop = asyncio.get_event_loop()
    results = asyncio.gather(*[start_websockets(e, loop) for e in investor.exchange_list], investor.get_market_data())
    loop.run_until_complete(results)
    loop.close()

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

plt.rcParams['figure.figsize'] = [7.50, 3.50]
plt.rcParams['figure.autolayout'] = True

app = Flask(__name__)


def plot(data, axis):
    """
    Plots nested list using pyplot

    Args:
        data (list): Nested list, with headings in first row
    """
    headings = data.pop(0)
    plot_data = list()
    for row in data:
        plot_row = [float(num) for num in row]
        if plot_row.count(0.0) < len(plot_row):
            plot_data.append(plot_row)
    plot_data = np.array(plot_data).T.tolist()
    for row in plot_data:
        axis.plot(row)


@app.route('/make-plot/<filename>')
def plot_png(filename):
    fig = Figure()
    csv_data = read_csv(filename)
    axis = fig.add_subplot(1, 1, 1)
    plot(csv_data, axis)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route("/")
def data():
    body = f"<p>Current account balances. USDT: {investors['BTC'].exchange_list[0].holdings['USDT']}, " \
           f"BTC: {investors['BTC'].exchange_list[0].holdings['BTC']}, " \
           f"ETH: {investors['ETH'].exchange_list[0].holdings['ETH']}</p><br>"
    for symbol in symbols_to_trade:
        body += f"<p>Current exchange discrepancies: {investors[symbol].get_current_disc()}</p>" \
                f"<p>Avg diff: {investors[symbol].avg_diff}</p><br>"
    for filename in os.listdir("./outputs/"):
        body += f"<a href='/get_data_csv/{filename}'>{filename.replace('_', ' ')}</a><br>" \
                f"<a href='/make-plot/{filename}'>{filename.replace('_', ' ')} -- Plot data</a><br><br>"
    body += "<br><br>"
    for filename in os.listdir("./outputs/"):
        body += f"<img src='/make-plot/{filename}'>"
    return f'''
        <html><body>
        {body}
        </body></html>
        '''


@app.route("/get_data_csv/<filename>")
def get_data_csv(filename):
    with open(f"./outputs/{filename}") as fp:
        csv = fp.read()
        print(csv)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"})


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
    def __init__(self, symbol: str, calibration_time: int, timestep: float, buy_disc: float, verbose_logging=False,
                 testnet=False):
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

        self.historical_bids = [[e.get_bid(symbol)] for e in self.exchange_list]
        self.fields = [e.name for e in self.exchange_list]
        self.diff_lists = [[e.get_bid(symbol) - self.exchange_list[0].get_bid(symbol)] for e in self.exchange_list]
        self.avg_diff = [e.get_bid(symbol) - self.exchange_list[0].get_ask(symbol) for e in self.exchange_list]
        self.current_disc = [self.diff_lists[e][-1] - self.avg_diff[e] for e in range(0,len(self.exchange_list))]
        self.loops_completed = 0
        self.invest_checks_completed = 0

    def get_symbol(self):
        return self.symbol

    def get_current_disc(self):
        return self.current_disc

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
                print(f"App: {self.symbol}: {time.ctime()} {bids} {self.loops_completed}")
            if self.loops_completed % 30 == 0:
                await self.exchange_list[0].update_account_balances()
                if self.loops_completed > self.calibration_loops:
                    self.historical_bids = self.historical_bids[-self.calibration_loops:]
                    self.diff_lists = self.diff_lists[-self.calibration_loops:]
                write_to_csv(f'bid_data_{self.symbol}', self.fields, self.historical_bids)
                write_to_csv(f'diffs_data_{self.symbol}', self.fields, self.diff_lists)
                self.historical_bids = [[e.get_bid(symbol)] for e in self.exchange_list]
                self.diff_lists = [[e.get_bid(symbol) - self.exchange_list[0].get_ask(symbol)]
                                   for e in self.exchange_list]
            for e in range(0, len(self.exchange_list)):
                self.historical_bids[e].append(self.exchange_list[e].get_bid(self.symbol))
                self.diff_lists[e].append(
                    self.exchange_list[e].get_bid(self.symbol) - self.exchange_list[0].get_ask(self.symbol))
                self.current_disc[e] = self.diff_lists[e][-1] - self.avg_diff[e]
                self.avg_diff[e] = self.avg_diff[e] * ((self.loops_completed - 1) / self.loops_completed) \
                                   + self.diff_lists[e][-1] / self.loops_completed


async def start_websockets(exchange, loop):
    while True:
        try:
            await exchange.start_websockets(loop)
        except Exception as e:
            print(f"{exchange.name} errored out: {e}. Restarting websocket...")


def run_app():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    if not os.path.exists("./outputs/"):
        os.mkdir("./outputs/")
    app_thread = threading.Thread(target=run_app)
    app_thread.start()
    symbols_to_trade = ["BTC", "ETH"]
    investors = dict()
    loop = asyncio.get_event_loop()
    coros = list()
    for symbol in symbols_to_trade:
        investors[symbol] = Investor(symbol=symbol,
                                     calibration_time=10000,
                                     timestep=0.5, buy_disc=0.0013,
                                     verbose_logging=True, testnet=False)
        coros.append(asyncio.gather(*[start_websockets(e, loop) for e in investors[symbol].exchange_list],
                                    investors[symbol].get_market_data()))
    results = asyncio.gather(*coros)
    loop.run_until_complete(results)
    loop.close()

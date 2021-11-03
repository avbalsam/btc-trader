import asyncio
import csv
import time
import numpy as np
import logging

from cryptoxlib.Pair import Pair
from cryptoxlib.version_conversions import async_run

from binance import Binance
from bitforex import Bitforex
from aax import AAX
from hitbtc import Hitbtc
from ku import KuCoin


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


# initialize all exchanges using their constructors
exchange_list = [Binance(testnet=False), AAX(), Hitbtc(), KuCoin()]

# LOG = logging.getLogger("cryptoxlib")
# LOG.setLevel(logging.INFO)
# LOG.addHandler(logging.StreamHandler())


async def get_market_data(symbol):
    fields = [exchange.name for exchange in exchange_list]
    historical_bids = [list() for i in range(0, len(exchange_list))]
    diff_lists = [list() for i in range(0, len(exchange_list))]
    avg_diff = [e.get_bid(symbol) - exchange_list[0].get_bid(symbol) for e in exchange_list]
    mean_diff = [list() for i in range(0, len(exchange_list))]
    await exchange_list[0].update_account_balances()
    # print(await exchange_list[0].get_profit(Pair('BTC', 'USDT'), commission=.00075))
    # print(len(await exchange_list[0].get_account_trades(Pair('BTC', 'USDT'))))
    # print(await exchange_list[0].print_trades(Pair('BTC', 'USDT')))
    # print(await exchange_list[0].get_profit(Pair('BTC', 'USDT')))
    # return
    x = 0
    while True:
        x += 1
        await asyncio.sleep(.05)
        bids = [e.get_bid(symbol) for e in exchange_list]
        if 0.0 in bids:
            x -= 1
            await asyncio.sleep(1)
            print(bids)
            continue
        print(f"{time.ctime()} {bids}")
        if x % 100 == 0:
            print("Current time: " + time.ctime())
            print(f"{str(x)} loops completed...")
            print(bids)
            print(avg_diff)
            print(f"Current holdings: {str(exchange_list[0].holdings)}")
            if x % 1000 == 0:
                await exchange_list[0].update_account_balances()
        buy_disc_count = 0
        sell_disc_count = 0
        for e in range(0, len(exchange_list)):
            historical_bids[e].append(exchange_list[e].get_bid(symbol))
            diff_lists[e].append(exchange_list[e].get_bid(symbol) - exchange_list[0].get_bid(symbol))
            if x <= 75000:
                avg_diff[e] = avg_diff[e] * ((x - 1) / x) + diff_lists[e][-1] / x
            else:
                avg_diff[e] = np.mean(diff_lists[e][-75000:])
            mean_diff[e].append(diff_lists[e][-1] - avg_diff[e])
            if mean_diff[e][-1] > 65:
                buy_disc_count += 1
            if mean_diff[e][-1] < 0:
                sell_disc_count += 1
        # print(f"{buy_disc_count} {sell_disc_count}")
        # TODO Move buy/sell checks into another async function to run in parallel with price data collection
        if x > 75000:
            if buy_disc_count == len(exchange_list)-2 and exchange_list[0].holdings['usdt'] > 0:
                try:
                    await exchange_list[0].buy_market()
                except Exception as e:
                    print(f"Out: {e}")
        if sell_disc_count == len(exchange_list)-2 and float(exchange_list[0].holdings['btc']) >= .001:
            try:
                await exchange_list[0].sell_market()
            except Exception as e:
                print(f"Out: {e}")


async def run(loop):
    await asyncio.gather(*[start_websockets(e, loop) for e in exchange_list], get_market_data())


async def start_websockets(exchange, loop):
    while True:
        try:
            await exchange.start_websockets(loop)
        except Exception as e:
            print(f"{exchange.name} errored out: {e}. Restarting websocket...")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    results = asyncio.gather(*[start_websockets(e, loop) for e in exchange_list], get_market_data('BTC'))
    loop.run_until_complete(results)

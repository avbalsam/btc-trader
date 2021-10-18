import asyncio
import csv
import time
import numpy as np
import logging

from cryptoxlib.version_conversions import async_run

from binance import Binance
from bitforex import Bitforex
from aax import AAX
from hitbtc import Hitbtc

from Investor import Investor


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
exchange_list = [Binance(), Bitforex(), AAX(), Hitbtc()]

# LOG = logging.getLogger("cryptoxlib")
# LOG.setLevel(logging.INFO)
# LOG.addHandler(logging.StreamHandler())


async def run(invest_length):
    try:
        await asyncio.gather(*[e.client.start_websockets() for e in exchange_list],
                             get_historical_bids(invest_length))
    except Exception as e:
        print(f"Error while starting websockets: {e}")
    while True:
        try:
            await asyncio.gather(*[e.client.start_websockets() for e in exchange_list])
            break
        except Exception as e:
            print(f"Error while restarting websockets {e}")
    try:
        await asyncio.gather(*[e.client.close() for e in exchange_list])
    except Exception as e:
        print(f"Out: {e}")


investors = [Investor("Maxwell", {"disc_count": 3, "disc_size": 70}, {"disc_count": 2, "disc_size": -5}),
             Investor("Leonard", {"disc_count": 3, "disc_size": 55}, {"disc_count": 2, "disc_size": -5}),
             Investor("Amanda", {"disc_count": 3, "disc_size": 70}, {"disc_count": 3, "disc_size": 10}),
             Investor("Ezra", {"disc_count": 3, "disc_size": 60}, {"disc_count": 2, "disc_size": -10})]


async def get_historical_bids(test_length):
    fields = [exchange.name for exchange in exchange_list]
    historical_bids = [list() for i in range(0, len(exchange_list))]
    diff_lists = [list() for i in range(0, len(exchange_list))]
    avg_diff = [e.get_bid() - exchange_list[0].get_bid() for e in exchange_list]
    mean_diff = [list() for i in range(0, len(exchange_list))]
    for x in range(1, test_length):
        await asyncio.sleep(.05)
        bids = [e.get_bid() for e in exchange_list]
        if 0.0 in bids:
            x -= 1
            # print(time.ctime() + str(bids))
            await asyncio.sleep(1)
            continue
        # print(time.ctime() + str(bids) + " btc")
        if x % 1000 == 0:
            print("Current time: " + time.ctime())
            print(f"{str(x)} loops completed...")
            print(bids)
            print(avg_diff)
            for investor in investors:
                print(investor.name + " transaction history: " + str(investor.transaction_history))
            write_to_csv("bid_data", fields, historical_bids)
            write_to_csv("diffs_data", fields, diff_lists)
            write_to_csv("mean_diffs_data", fields, mean_diff)
            write_to_csv("investors_data", [investor.name for investor in investors], [investor.transaction_history for investor in investors])
        for e in range(0, len(exchange_list)):
            historical_bids[e].append(exchange_list[e].get_bid())
            diff_lists[e].append(exchange_list[e].get_bid() - exchange_list[0].get_bid())
            if x <= 75000:
                avg_diff[e] = avg_diff[e] * ((x - 1) / x) + diff_lists[e][-1] / x
            else:
                avg_diff[e] = np.mean(diff_lists[e][-75000:])
            mean_diff[e].append(diff_lists[e][-1] - avg_diff[e])
        if x > 30000:
            for investor in investors:
                investor.invest(mean_diff, exchange_list[0].get_ask(), exchange_list[0].get_bid(), commission=.00075)

if __name__ == "__main__":
    async_run(run(500000))

from Exchange import Bitflyer, ItBit, Gemini, Bittrex, HitBtc, Binance, Robinhood, Coinbase
import time, os, csv
# from matplotlib import pyplot as plt
from statistics import mean
import robin_stocks.robinhood as r
import threading


def write_to_csv(filename, fields, data):
    """
    Writes input data to csv file.

    Args:
        filename (str): Do not include .csv extension.
        fields (list): First row of table.
        data (list): Nested list. Each element represents one row.
    """
    try:
        with open("data/" + filename + ".csv", "w") as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(data)
    except PermissionError:
        print("Unable to gain access to file. Please close any programs which are using " + filename + ".csv...")


# initialize all exchanges using their constructors
exchange_list = [Binance(), HitBtc(), Coinbase(), Gemini()]


def get_historical_bids(test_length):
    fields = [exchange.name for exchange in exchange_list]
    historical_bids = [list() for i in range(0,len(exchange_list))]
    diff_lists = [list() for i in range(0,len(exchange_list))]
    avg_diff = [float() for i in range(0,len(exchange_list))]
    mean_diff = [list() for i in range(0,len(exchange_list))]
    for x in range(0, test_length):
        time.sleep(.1)
        if x % 100 == 0 and x != 0:
            print(str(x) + " loops completed. Writing collected data to csv...")
            write_to_csv("bid_data", fields, historical_bids)
            write_to_csv("diffs_data", fields, diff_lists)
            write_to_csv("mean_diffs_data", fields, mean_diff)
        bids = [e.get_bid() for e in exchange_list]
        print(bids)
        for e in range(0, len(exchange_list)):
            historical_bids[e].append(exchange_list[e].get_bid())
            diff_lists[e].append(exchange_list[e].get_bid() - exchange_list[0].get_bid())
            avg_diff[e] = mean(diff_lists[e])
            mean_diff[e].append(diff_lists[e][-1] - avg_diff[e])
        # TODO Create restart stream method for every exchange and check each one with for loop
        if exchange_list[0].stream_error:
            exchange_list[0].restart_stream()


print("Waiting for websockets to connect...")
while 0.0 in [e.get_bid() for e in exchange_list]:
    pass

get_historical_bids(18000)

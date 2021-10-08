import csv
import time
from statistics import mean
from Exchange import Gemini, HitBtc, Binance, Coinbase
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
        with open("data/" + filename + ".csv", "w") as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(data)
    except PermissionError:
        print("Unable to gain access to file. Please close any programs which are using " + filename + ".csv...")


# initialize all exchanges using their constructors
exchange_list = [Binance(), HitBtc(), Coinbase(), Gemini()]

investors = [Investor("Maxwell", {"disc_count": 3, "disc_size": 50}, {"disc_count": 3, "disc_size": 0}),
             Investor("Leonard", {"disc_count": 3, "disc_size": 60}, {"disc_count": 3, "disc_size": -5}),
             Investor("Amanda", {"disc_count": 2, "disc_size": 65}, {"disc_count": 3, "disc_size": 0})]


def get_historical_bids(test_length):
    fields = [exchange.name for exchange in exchange_list]
    historical_bids = [list() for i in range(0,len(exchange_list))]
    diff_lists = [list() for i in range(0,len(exchange_list))]
    avg_diff = [float() for i in range(0,len(exchange_list))]
    mean_diff = [list() for i in range(0,len(exchange_list))]
    for x in range(0, test_length):
        time.sleep(.1)
        bids = [e.get_bid() for e in exchange_list]
        if x % 1000 == 0 and x != 0:
            print(str(x) + " loops completed. Writing collected data to csv...")
            print(bids)
            write_to_csv("bid_data", fields, historical_bids)
            write_to_csv("diffs_data", fields, diff_lists)
            write_to_csv("mean_diffs_data", fields, mean_diff)
        for e in range(0, len(exchange_list)):
            historical_bids[e].append(exchange_list[e].get_bid())
            diff_lists[e].append(exchange_list[e].get_bid() - exchange_list[0].get_bid())
            avg_diff[e] = mean(diff_lists[e])
            mean_diff[e].append(diff_lists[e][-1] - avg_diff[e])
        # TODO Create restart stream method for every exchange and check each one with for loop
        if exchange_list[0].stream_error:
            exchange_list[0].restart_stream()
            continue
        for investor in investors:
            investor.invest(mean_diff, exchange_list[0].get_ask(), exchange_list[0].get_bid(), commission=.00075)


print("Waiting for websockets to connect...")
while 0.0 in [e.get_bid() for e in exchange_list]:
    pass

get_historical_bids(72000)

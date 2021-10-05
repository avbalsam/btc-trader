from Exchange import Bitflyer, ItBit, Gemini, Bittrex, HitBtc, Binance, Robinhood, Coinbase
import time, os, csv
# from matplotlib import pyplot as plt
from statistics import mean
import robin_stocks.robinhood as r


def write_to_csv(filename, fields, data):
    """
    Writes input data to csv file.

    Args:
        filename (str): Do not include .csv extension.
        fields (list): First row of table.
        data (list): Nested list. Each element represents one row.
    """
    with open("data/" + filename + ".csv", "w") as f:
        write = csv.writer(f)
        write.writerow(fields)
        write.writerows(data)


# initialize all exchanges using their constructors
exchange_list = [Binance(), HitBtc(), Coinbase(), Gemini()]

print("Waiting for websockets to connect...")
while 0.0 in [e.get_bid() for e in exchange_list]:
    pass

# calls api "iterations" times and calculates expected difference between first exchange and each other exchange
# returns avg_diffs, a list of the expected differences in price between the first exchange and each other exchange
def invest(init_length, invest_length, buy_discrepancy, sell_discrepancy, verbose_logging):
    investing = False
    buy_price = None
    transaction_gains = list()
    total_percent_gain = 0
    total_percent_gain_no_fees = 0
    transaction_count = 0
    ask_lists = list()
    bid_lists = list()
    current_price = None
    last_price = None

    # initialize values
    print("Initializing model...")
    while len(bid_lists) < init_length:
        time.sleep(.1)
        if len(bid_lists) % int(init_length/10) == 0:
            print("Initializing model... " + str(round(len(bid_lists)/init_length*100)) + "%")
        try:
            bid_list = [x.get_bid() for x in exchange_list]
            ask_list = [x.get_ask() for x in exchange_list]
            bid_list.append(mean(bid_list))
            ask_lists.append(ask_list)
            bid_lists.append(bid_list)
        except:
            print("Error collecting price.")
    bids_over_time = list()
    asks_over_time = list()
    for el_num in range(0, len(bid_lists[0])):
        bid = [bid_list[el_num] for bid_list in bid_lists]
        bids_over_time.append(bid)

    #TODO make this for loop work
    """for el_num in range(0, len(ask_lists[0])):
        ask = [ask_list[el_num] for ask_list in ask_lists]
        asks_over_time.append(ask)"""
    diff_lists = [[bids_over_time[0][el] - bid_list[el] for el in range(0, len(bid_list))] for bid_list in
                  bids_over_time]
    avg_diffs = list()
    mean_diff = list()
    for diff_list in range(0, len(diff_lists)):
        avg_diff = mean(diff_lists[diff_list])
        # avg_diff = avg_diffs[diff_list]
        avg_diffs.append(avg_diff)
        mean_diff.append([el - avg_diff for el in diff_lists[diff_list]])
    print("Initialization complete...")
    print(avg_diffs)

    # After calculating avg_diff, begin investment process
    for x in range(0, invest_length):
        time.sleep(.1)
        if x % 100 == 0:
            print(str(x) + " loops completed. Total profit so far: " + str(total_percent_gain))
            if len(transaction_gains) > 0:
                print("Average profit per transaction: " + str(mean(transaction_gains)))
        try:
            bid_list = [x.get_bid() for x in exchange_list]
            ask_list = [x.get_ask() for x in exchange_list]
        except:
            print("Error collecting prices")
            continue
        ask_list.append(mean(ask_list[1:]))
        bid_list.append(mean(bid_list[1:]))
        ask_lists.append(ask_list)
        bid_lists.append(bid_list)

        # calculate deviation of each exchange from mean deviation
        for i in range(0, len(bid_list)):
            bids_over_time[i].append(bid_list[i])
            #asks_over_time[i].append(ask_list[i])
            diff_lists[i].append(bids_over_time[0][-1] - bids_over_time[i][-1])
            avg_diffs[i] = mean(diff_lists[i][-1*(init_length-20):])
            mean_diff[i].append(diff_lists[i][-1] - avg_diffs[i])

        last_price = bids_over_time[0][-2]
        current_price = bids_over_time[0][-1]

        buy_disc_count = 0
        sell_disc_count = 0
        lower_count = 0
        for i in range(0, len(diff_lists)):
            if mean_diff[i][-1] <= buy_discrepancy:
                buy_disc_count += 1
            if mean_diff[i][-1] >= sell_discrepancy:
                sell_disc_count += 1
            if mean_diff[i][-1] < -10:
                lower_count += 1
        # if currently investing, check to see if it's a good time to sell
        if investing:
            if sell_disc_count >= 5 and mean_diff[-1][-1] > -7:
                print("Selling bitcoin now.")
                #exchange_list[0].sell_market(.0001)
                sell_price = exchange_list[0].get_bid()
                print("Sell price: " + str(sell_price))
                print("Buy price: " + str(buy_price))
                percent_gain_no_fees = (sell_price - buy_price) / buy_price * 100
                buy_price = buy_price + buy_price * .00075
                sell_price = sell_price - sell_price * .00075
                percent_gain = (sell_price - buy_price) / buy_price * 100
                transaction_gains.append(percent_gain)
                print("Total profit: " + str(percent_gain) + "%")
                total_percent_gain += percent_gain
                total_percent_gain_no_fees += percent_gain_no_fees
                investing = False
                buy_price = None
                transaction_count += 1
        elif buy_disc_count >= 5 or mean_diff[-1][-1] <= -45:
            print("Exchange discrepancy detected. Buying bitcoin now.")
            investing = True
            #exchange_list[0].buy_market(.0001)
            buy_price = exchange_list[0].get_ask()
            print("Buy price: " + str(buy_price))
        if verbose_logging:
            print([round(diff[-1], 2) for diff in mean_diff])
            print("Price change: " + str(current_price-last_price))
    print("Investment period concluded. A total of " + str(transaction_count) + " transactions were conducted.")
    print("With transaction fees of 0.075%, total profit was " + str(total_percent_gain) +
          "%. Without transaction fees, total profits would have been " + str(total_percent_gain_no_fees) + "%.")

    fields = [exchange.name for exchange in exchange_list]
    fields.append("Mean")

    write_to_csv("bid_data", fields, bids_over_time)

    write_to_csv("diffs_data", fields, diff_lists)

    write_to_csv("mean_diffs_data", fields, mean_diff)


invest(1000, 40000, -75, -30, False)

from typing import List, Any

from Exchange import Bitflyer, ItBit, Gemini, Bittrex, HitBtc, Binance, Robinhood
import time
from matplotlib import pyplot as plt
from statistics import mean
import robin_stocks.robinhood as r

# initialize all exchanges using their constructors
exchangeList = [Robinhood(), Bitflyer(), Gemini(), ItBit(), Binance()]

plotList = list()
plotList1 = list()


# calls api "iterations" times and calculates expected difference between first exchange and each other exchange
# returns avg_diffs, a list of the expected differences in price between the first exchange and each other exchange
def invest(init_length, invest_length, buy_discrepancy, sell_discrepancy):
    investing = False
    buy_price = None
    total_percent_gain = 0
    total_percent_gain_no_fees = 0
    transaction_count = 0
    ask_lists = list()
    bid_lists = list()
    current_price = None
    last_price = None

    # initialize values
    print("Initializing model...")
    for x in range(0, init_length):
        try:
            bid_list = [x.get_bid() for x in exchangeList]
            #ask_list = [x.get_ask() for x in exchangeList]
            ask_list = []
            #ask_list.append(mean(ask_list))
            bid_list.append(mean(bid_list))
            print(bid_list)
            ask_lists.append(ask_list)
            bid_lists.append(bid_list)
        except:
            print("Error collecting price")
        time.sleep(.1)
    bids_over_time = list()
    for el_num in range(0, len(bid_lists[0])):
        bid = [bid_list[el_num] for bid_list in bid_lists]
        bids_over_time.append(bid)
        plt.plot(bid, label="Exchange " + str(el_num))
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
        try:
            bid_list = [x.get_bid() for x in exchangeList]
            ask_list = [x.get_ask() for x in exchangeList]
        except:
            print("Error collecting prices")
            continue
        # bid_list.sort(reverse=True)
        # ask_list.sort()
        ask_list.append(mean(ask_list[1:]))
        bid_list.append(mean(bid_list[1:]))
        print(bid_list)
        ask_lists.append(ask_list)
        bid_lists.append(bid_list)

        # calculate deviation of each exchange from mean deviation
        for i in range(0, len(bid_list)):
            bids_over_time[i].append(bid_list[i])
            diff_lists[i].append(bids_over_time[0][-1] - bids_over_time[i][-1])
            avg_diffs[i] = mean(diff_lists[i])
            mean_diff[i].append(diff_lists[i][-1] - avg_diffs[i])
        print(avg_diffs)

        last_price = bids_over_time[0][-2]
        current_price = bids_over_time[0][-1]

        buy_disc_count = 0
        sell_disc_count = 0
        for i in range(0, len(diff_lists)):
            if mean_diff[i][-1] <= buy_discrepancy:
                buy_disc_count += 1
            if mean_diff[i][-1] >= sell_discrepancy:
                sell_disc_count += 1
        # if currently investing, check to see if it's a good time to sell
        if investing:
            if sell_disc_count >= 2 and mean_diff[-1][-1] > -7:
                print("Selling bitcoin now.")
                sell_price = current_price
                print("Sell price: " + str(sell_price))
                print("Buy price: " + str(buy_price))
                percent_gain_no_fees = (sell_price - buy_price) / buy_price * 100
                buy_price = buy_price + buy_price * .00075
                sell_price = sell_price - sell_price * .00075
                percent_gain = (sell_price - buy_price) / buy_price * 100
                print("Total profit: " + str(percent_gain) + "%")
                total_percent_gain += percent_gain
                total_percent_gain_no_fees += percent_gain_no_fees
                investing = False
                buy_price = None
                transaction_count += 1
        elif buy_disc_count >= 2 or mean_diff[-1][-1] <= -30:
            print("Exchange discrepancy detected. Buying bitcoin now.")
            investing = True
            buy_price = current_price
            print("Buy price: " + str(buy_price))
        print("Discrepancy count: " + str(buy_disc_count))
        print([diff[-1] for diff in mean_diff])
        print("Robinhood price change: " + str((current_price - last_price)/current_price * 100) + "%. Robinhood price: " +
              str(current_price))
        print("\n")
    print("Investment period concluded. A total of " + str(transaction_count) + " transactions were conducted.")
    print("With transaction fees of 0.075%, total profit was " + str(total_percent_gain) +
          "%. Without transaction fees, total profits would have been " + str(total_percent_gain_no_fees) + "%.")


def plot_price_diff():
    ask_lists = list()
    bid_lists = list()
    for x in range(0, 20):
        try:
            bid_list = [x.get_bid() for x in exchangeList]
            ask_list = [x.get_ask() for x in exchangeList]
            # bid_list.sort(reverse=True)
            # ask_list.sort()
            ask_list.append(mean(ask_list))
            bid_list.append(mean(bid_list))
            print(bid_list)
            ask_lists.append(ask_list)
            bid_lists.append(bid_list)
        except:
            print("Error collecting price")
        time.sleep(.1)
    bids_over_time = list()
    for el_num in range(0, len(bid_lists[0])):
        bid = [bid_list[el_num] for bid_list in bid_lists]
        bids_over_time.append(bid)
        plt.plot(bid, label="Exchange " + str(el_num))
    diff_lists = [[bids_over_time[0][el] - bid_list[el] for el in range(0, len(bid_list))] for bid_list in
                  bids_over_time]
    print(diff_lists)
    mean_diff = list()
    # avg_diffs = [0.0, -72.42238200000114, 84.23898466666482, 3.9388675555550434]
    avg_diffs = list()
    for diff_list in range(0, len(diff_lists)):
        avg_diff = mean(diff_lists[diff_list])
        # avg_diff = avg_diffs[diff_list]
        avg_diffs.append(avg_diff)
        mean_diff.append([el - avg_diff for el in diff_lists[diff_list]])
    for diff in mean_diff:
        print(diff)
    print(avg_diffs)
    # plt.plot(mean_diff[1])
    # plt.plot(mean_diff[2])
    print("\n\n")

    high_diff_count = 0
    total_percent_gain = 0
    for diff_list in range(0, len(mean_diff)):
        for i in range(0, len(mean_diff[diff_list]) - 1):
            if mean_diff[diff_list][i] <= -30:
                high_diff_count += 1
                print("Exchange discrepancy detected at t=" + str(i) + ". This is discrepancy number " +
                      str(high_diff_count) + ":")
                print("Gemini bid price: " + str(bids_over_time[0][i]) + ", next bid price: " +
                      str(bids_over_time[0][i + 1]))
                print("Exchange " + str(diff_list) + " bid price: " + str(bids_over_time[diff_list][i]) +
                      ", next bid price: " + str(bids_over_time[diff_list][i + 1]))
                print("Price difference: " + str(avg_diffs[diff_list]))
                # print("Bitflyer next ask price: " + str(ask_lists[diff_list][i+1]))
                current_price = bids_over_time[0][i]
                next_price = bids_over_time[0][i + 1]
                if current_price != next_price:
                    percent_gain = (next_price - current_price) / abs(current_price) * 100 - 0.1
                else:
                    percent_gain == 0
                total_percent_gain += percent_gain
                if percent_gain > 0:
                    print("The investment would have been a success, with a total gain of " + str(percent_gain) + "%")
                else:
                    print("The investment would have been a failure, with a total loss of " + str(percent_gain) + "%")
                print("\n")
                break
    print("Investment period finished. A total of " + str(high_diff_count) +
          " transactions were performed for a total profit of " + str(total_percent_gain) + "%.")
    plt.show()


invest(5, 500, -18, -10)


r.logout()

from Exchange import Bitflyer, ItBit, Gemini, Bittrex, HitBtc, Binance, Robinhood
import time
#from matplotlib import pyplot as plt
from statistics import mean
import robin_stocks.robinhood as r

# initialize all exchanges using their constructors
exchange_list = [Robinhood(), Bitflyer(), Gemini(), ItBit(), Binance(), HitBtc(), Bittrex()]


# calls api "iterations" times and calculates expected difference between first exchange and each other exchange
# returns avg_diffs, a list of the expected differences in price between the first exchange and each other exchange
def invest(init_length, invest_length, buy_discrepancy, sell_discrepancy, verbose_logging):
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
            exchange_list.reverse()
            bid_list = [x.get_bid() for x in exchange_list]
            exchange_list.reverse()
            bid_list.reverse()
            # ask_list = [x.get_ask() for x in exchange_list]
            ask_list = []
            # ask_list.append(mean(ask_list))
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
        #plt.plot(bid, label="Exchange " + str(el_num))
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
        if x % 10 == 0:
            print(str(x) + " loops completed. Total profit so far: " + str(total_percent_gain_no_fees))
        try:
            bid_list = [x.get_bid() for x in exchange_list]
            ask_list = [x.get_ask() for x in exchange_list]
        except:
            print("Error collecting prices")
            continue
        # bid_list.sort(reverse=True)
        # ask_list.sort()
        ask_list.append(mean(ask_list[1:]))
        bid_list.append(mean(bid_list[1:]))
        #print(bid_list)
        ask_lists.append(ask_list)
        bid_lists.append(bid_list)

        # calculate deviation of each exchange from mean deviation
        for i in range(0, len(bid_list)):
            bids_over_time[i].append(bid_list[i])
            diff_lists[i].append(bids_over_time[0][-1] - bids_over_time[i][-1])
            avg_diffs[i] = mean(diff_lists[i])
            mean_diff[i].append(diff_lists[i][-1] - avg_diffs[i])
        #print(avg_diffs)

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
            if mean_diff[i][-1] < -5:
                lower_count += 1
        # if currently investing, check to see if it's a good time to sell
        if investing:
            if sell_disc_count >= 2 and mean_diff[-1][-1] > -7 and lower_count < len(exchange_list):
                print("Selling bitcoin now.")
                sell_price = exchange_list[0].get_bid()
                print("Sell price: " + str(sell_price))
                print("Buy price: " + str(buy_price))
                percent_gain_no_fees = (sell_price - buy_price) / buy_price * 100
                # buy_price = buy_price + buy_price * .00075
                # sell_price = sell_price - sell_price * .00075
                percent_gain = (sell_price - buy_price) / buy_price * 100
                print("Total profit: " + str(percent_gain) + "%")
                total_percent_gain += percent_gain
                total_percent_gain_no_fees += percent_gain_no_fees
                # r.sell_crypto_by_price("BTC", 1 + percent_gain_no_fees / 100)
                investing = False
                buy_price = None
                transaction_count += 1
        elif buy_disc_count >= 2 or mean_diff[-1][-1] <= -30 or lower_count == len(exchange_list)-1:
            print("Exchange discrepancy detected. Buying bitcoin now.")
            # r.order_buy_crypto_by_price('BTC', 1)
            investing = True
            buy_price = exchange_list[0].get_bid()
            print("Buy price: " + str(buy_price))
        #print("Discrepancy count: " + str(buy_disc_count))
        if verbose_logging:
            print([round(diff[-1], 2) for diff in mean_diff])
        #print("Robinhood price change: " + str(
        #    (current_price - last_price) / current_price * 100) + "%. Robinhood price: " +
        #      str(current_price))
        #print("\n")
    print("Investment period concluded. A total of " + str(transaction_count) + " transactions were conducted.")
    print("With transaction fees of 0.075%, total profit was " + str(total_percent_gain) +
          "%. Without transaction fees, total profits would have been " + str(total_percent_gain_no_fees) + "%.")

invest(5, 1000000, -18, -10, False)

r.logout()

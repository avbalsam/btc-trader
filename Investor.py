import time


class Investor:
    def __init__(self, name, buy_criteria, sell_criteria, live_trading=False, commission=.00075):
        """
        Args:
            name (str): Name of investor
            buy_criteria (dict): {disc_count: int(), disc_size: float()}
                disc_count (int): Number of discrepancies needed for exchange to buy.
                disc_size (float): Size of discrepancy needed to be considered a discrepancy.
            sell_criteria (dict): {disc_count: int(), disc_size: int()}
                disc_count (int): Number of discrepancies needed for exchange to sell.
                disc_size (float): Size of discrepancy needed to be considered a discrepancy.
            live_trading (bool): Whether or not the investor will trade with real money
            commission (float): Amount of commission per transaction in decimal form (not percentage)
        """
        self.name = name
        self.live_trading = live_trading
        self.holdings = {'usdt': 1000, 'btc': 0}
        self.holding_crypto = False
        self.buy_criteria = buy_criteria
        self.sell_criteria = sell_criteria
        self.crypto_holdings = 0
        self.transaction_history = list()
        self.commission = commission

    def invest(self, mean_diff, ask_price, bid_price):
        """
        Check investor strategy and current price discrepancies, and decide whether investor will buy, sell, or hold.

        Args:
            mean_diff (list): Current price discrepancies for each exchange (same as in Main.py)
            ask_price (float): Current ask price of bitcoin
            bid_price (float): Current bid price of bitcoin
            commission (float): Current commission based on trading volume
        """
        if self.holding_crypto is False:
            disc_count = 0
            for m in mean_diff:
                if m[-1] > self.buy_criteria['disc_size']:
                    disc_count += 1
            if disc_count >= self.buy_criteria['disc_count']:
                self.usdt_to_btc(ask_price, self.commission)
                self.holding_crypto = True
        else:
            disc_count = 0
            for m in mean_diff:
                if m[-1] < self.sell_criteria['disc_size']:
                    disc_count += 1
            if disc_count >= self.sell_criteria['disc_count']:
                self.btc_to_usdt(bid_price, self.commission)
                self.holding_crypto = False

    def usdt_to_btc(self, ask_price, commission=.00075):
        """
        Simulate investor trading usdt for btc.

        Args:
            ask_price (float): Current ask price of bitcoin. Make sure to pass ask price, not spot or bid.
            commission (float): Commission fees at current trade volume. Do not pass a percentage to this function.
        """
        self.holding_crypto = True
        usdt = self.holdings['usdt']
        btc_value = (usdt - usdt * commission) / ask_price
        self.holdings['usdt'] -= usdt
        self.holdings['btc'] += btc_value
        print(self.name + " spent " + str(usdt) + " dollars in USDT to buy " + str(btc_value) +
              " bitcoins.\nTotal holdings: " + str(self.holdings))
        self.transaction_history.append({'time': time.ctime(), 'transaction': 'usdt_to_btc', 'usdt': usdt, 'btc': btc_value})

    def btc_to_usdt(self, bid_price, commission=.00075):
        """
        Simulate investor trading btc for usdt.

        Args:
            bid_price (float): Current bid price of bitcoin. Make sure to pass bid price, not spot or ask.
            commission (float): Commission fees at current trade volume. Do not pass a percentage to this function.
        """
        self.holding_crypto = False
        btc = self.holdings['btc']
        usdt_value = (btc - btc * commission) * bid_price
        self.holdings['btc'] -= btc
        self.holdings['usdt'] += usdt_value
        print(self.name + " spent " + str(btc) + " bitcoins to buy " + str(usdt_value) + " USDT.\nTotal holdings: " +
              str(self.holdings))
        self.transaction_history.append({'time': time.ctime(), 'transaction': 'btc_to_usdt', 'usdt': usdt_value, 'btc': btc})

    def get_balance(self, symbol):
        """
        Get current balance of specified asset.

        Args:
            symbol (str): Symbol of asset to get balance of

        Returns:
            balance (int): Current balance of specified asset
        """
        return self.holdings[symbol]

    def get_transaction_history(self):
        """
        Get transaction history of trading bot

        Returns:
            transaction_history (list): History of all transactions made by bot.
                {'transaction': 'btc_to_usdt' or 'usdt_to_btc', 'usdt': usdt bought /sold, 'btc': btc bought / sold}
        """
        return self.transaction_history

class Investor:
    def __init__(self, buy_criteria, sell_criteria):
        """
        Args:
            buy_criteria (dict): {discrepancy_count: int(), discrepancy_size: int()}
            sell_criteria (dict): {discrepancy_count: int(), discrepancy_size: int()}
        """
        self.holdings = {'usdt': 100, 'btc': 0}
        self.buy_criteria = buy_criteria
        self.sell_criteria = sell_criteria
        self.crypto_holdings = 0

    def usdt_to_btc(self, ask_price, commission):
        """
        Simulate investor trading usdt for btc.

        Args:
            ask_price (float): Current ask price of bitcoin. Make sure to pass ask price, not spot or bid.
            commission (float): Commission fees at current trade volume. Do not pass a percentage to this function.
        """
        usdt = self.holdings['usdt']
        btc_value = (usdt - usdt * commission) / ask_price
        self.holdings['usdt'] -= usdt
        self.holdings['btc'] += btc_value
        print(str(usdt) + " dollars in USDT spent to buy " + str(btc_value) + " bitcoins.\nTotal holdings: " + str(
            self.holdings))

    def btc_to_usdt(self, bid_price, commission):
        """
        Simulate investor trading btc for usdt.

        Args:
            bid_price (float): Current bid price of bitcoin. Make sure to pass bid price, not spot or ask.
            commission (float): Commission fees at current trade volume. Do not pass a percentage to this function.
        """
        btc = self.holdings['btc']
        usdt_value = (btc - btc * commission) * bid_price
        self.holdings['btc'] -= btc
        self.holdings['usdt'] += usdt_value
        print(str(btc) + " bitcoins spent to buy " + str(usdt_value) + " USDT.\nTotal holdings: " + str(
            self.holdings))

    def get_balance(self, symbol):
        """
        Get current balance of specified asset.

        Args:
            symbol (str): Symbol of asset to get balance of

        Returns:
            balance (int): Current balance of specified asset
        """
        return self.holdings[symbol]
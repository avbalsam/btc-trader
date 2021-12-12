from symbol import Symbol


class Exchange:
    """Superclass which includes get_bid(), get_ask(), and invest() methods"""
    def __init__(self):
        self.best_ask_by_symbol = dict()
        self.best_bid_by_symbol = dict()

    def get_ask(self, symbol) -> float:
        if type(symbol) == Symbol:
            symbol = symbol.get_name()
        if symbol in self.best_ask_by_symbol:
            return float(self.best_ask_by_symbol[symbol])
        else:
            return 0.0

    def get_bid(self, symbol) -> float:
        if type(symbol) == Symbol:
            symbol = symbol.get_name()
        if symbol in self.best_bid_by_symbol:
            return float(self.best_bid_by_symbol[symbol])
        else:
            return 0.0

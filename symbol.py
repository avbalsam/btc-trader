import requests


class Symbol:
    def __init__(self, name: str, min_precision: float, min_order_size: float):
        """
        Args:
            name (str): The name of the symbol
            min_precision (float): The maximum number of digits after the decimal allowed when setting LOT_SIZE
            min_order_size (float): Minimum buy/sell amount, in base asset (not USDT)
        """
        self.name = name
        self.min_precision = min_precision
        self.min_order_size = min_order_size

    def get_name(self):
        return self.name

    def get_min_precision(self):
        return self.min_precision

    def get_min_order_size(self):
        return float(self.min_order_size)

    def __str__(self):
        return f"Symbol {self.name}. Precision: {self.min_precision}, Min order: {self.min_order_size}"


def convert_to_symbol(symbol_names: list):
    """
    Converts a list of symbol names into a list of Symbol objects by using a Binance api call to determine important
    information about every symbol in the list.

    Args:
        symbol_names (list): List of symbol names

    Returns:
        symbols (list): List of Symbol objects
    """
    symbols_to_trade = list()
    symbol_params = "%5B"
    for name in symbol_names:
        symbol_params += f"%22{name}USDT%22,"
    symbol_params = symbol_params[:-1]
    symbol_params += "%5D"
    r = requests.get(f"https://api.binance.com/api/v3/exchangeInfo?symbols={symbol_params}")
    response = r.json()
    for symbol in response["symbols"]:
        min_precision = None
        min_buy_amt = None
        for f in symbol['filters']:
            if f['filterType'] == 'LOT_SIZE':
                min_precision = f['minQty'].index("1") - 1
                if min_precision < 0:
                    min_precision = 0
                min_buy_amt = f['minQty']
        if min_precision is None or min_buy_amt is None:
            exit(400)
        symbols_to_trade.append(
            Symbol(name=symbol['baseAsset'], min_precision=min_precision, min_order_size=min_buy_amt))
    return symbols_to_trade

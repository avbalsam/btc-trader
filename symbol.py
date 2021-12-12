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
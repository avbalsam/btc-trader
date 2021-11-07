class Exchange:
    def __init__(self, investor):
        self.investor = investor
        self.best_ask_by_symbol = dict()
        self.best_bid_by_symbol = dict()

    def get_ask(self, symbol: str) -> float:
        if symbol in self.best_ask_by_symbol:
            return float(self.best_ask_by_symbol[symbol])
        else:
            return 0.0

    def get_bid(self, symbol: str):
        if symbol in self.best_bid_by_symbol:
            return float(self.best_bid_by_symbol[symbol])
        else:
            return 0.0

    async def invest(self):
        await self.investor.invest()

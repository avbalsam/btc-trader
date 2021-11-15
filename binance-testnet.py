import logging
import os

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.binance import enums
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.binance.exceptions import BinanceException
from cryptoxlib.version_conversions import async_run

LOG = logging.getLogger("cryptoxlib")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}")


async def run():
    api_key = "VCEnHDaubZwJkv7H61ivIoa2yBrFBJKc9UOR6bLx2ciTQHH75NcNrLuCpwjdDH0B"
    sec_key = "9XlcXTFRSYJG6LrRMt8nzjZJsfz0g6C6XpYNSHuKoEvoot6qybNXuaM7jyGcZ5Ge"

    client = CryptoXLib.create_binance_testnet_client(api_key, sec_key)

    print("Ping:")
    await client.ping()

    print("Server time:")
    await client.get_time()

    print("Exchange info:")
    await client.get_exchange_info()

    print("Create market order:")
    await client.create_order(Pair("BTC", "USDT"), side=enums.OrderSide.SELL, type=enums.OrderType.MARKET,
                              quantity="0.4",
                              new_order_response_type=enums.OrderResponseType.FULL)

    print("Get open orders:")
    await client.get_open_orders(pair=Pair('BTC', 'USDT'))

    print("Get all orders:")
    await client.get_all_orders(pair=Pair('BTC', 'USDT'))

    print("Account:")
    await client.get_account(recv_window_ms=5000)


if __name__ == "__main__":
    async_run(run())

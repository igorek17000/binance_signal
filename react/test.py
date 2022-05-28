import binance.client
from binance.client import Client

client = Client()

counter = 0
for i in client.futures_exchange_info()['symbols']:

    if "USDT" in i['symbol']:
        counter += 1
        print(i['symbol'])

print(counter)
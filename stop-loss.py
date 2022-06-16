from binance import ThreadedWebsocketManager
from binance.client import Client
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "binance_signal.settings")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rest.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
# your imports, e.g. Django models
from react.models import Setting

pub = 'TmCZsJp55qJPOWgleRLsWv8VBmFq4BIBQMCy2nWQI4t48fTT7x6ums4keMXL7Azv'
pri = 'sYMXl1urFA8TlU71BvV4JeDAcs3r89bXFou2vDVDQNhudo7hW4oNJ6QNRqUb9iCG'
current_symbols = {}
counter = 100



def convert_to_dict(symbols: list):
    result_dict = {}
    for i in symbols:

        if i['symbol'] in result_dict.keys() and float(i['stopPrice']) > float(result_dict[i['symbol']]['stopPrice']):
            result_dict[i['symbol']] = i
        elif i['symbol'] not in result_dict.keys():
            result_dict[i['symbol']] = i
    return result_dict


def get_setting():
    setting = Setting.objects.get(id=1)
    stop_loss = setting.stop_loss_for_rearrangement
    stop_loss_signal = setting.stop_signal
    return stop_loss, stop_loss_signal


def main():
    symbol = 'BNBBTC'
    client_bin = Client(pub, pri)
    exchange = convert_to_dict(client_bin.futures_exchange_info()['symbols'])
    twm = ThreadedWebsocketManager(api_key=pub, api_secret=pri)
    # start is required to initialise its internal loop
    twm.start()

    def create_order(target_symbol, stop_price):
        client_bin.futures_create_order(symbol=target_symbol,
                                        side='SELL',
                                        positionSide='BOTH',
                                        type='STOP_MARKET',
                                        closePosition='true',
                                        timeInForce='GTC',
                                        stopPrice=str(stop_price))

    def delete_order(target_symbol, order_id):
        client_bin.futures_cancel_order(symbol=target_symbol,
                                        orderId=order_id)

    def handle_socket_message(msg):
        global current_symbols
        global counter
        print(current_symbols)
        counter += 1
        print(f'new handle - {msg}')
        symbols = []
        if counter > 20:
            counter = 0
            for i in client_bin.futures_get_open_orders():
                if i['type'] == 'STOP_MARKET':
                    if i['stopPrice'] not in current_symbols:
                        current_symbols[i['symbol']] = [float(i['stopPrice']), i['orderId'], float(i['stopPrice']), 1]
                        twm.stop()
                        new_streams = ['bnbbtc@miniTicker']
                        for current_symbol in current_symbols.keys():
                            new_streams.append(f'{current_symbol.lower()}@miniTicker')
                        twm.start_multiplex_socket(callback=handle_socket_message, streams=new_streams)
                    symbols.append(i['symbol'])
            for i in list(current_symbols.keys()):
                if i not in symbols:
                    del current_symbols[i]
            if msg['data']['s'] not in symbols:
                if msg['data']['s'] != "BNBBTC":
                    twm.stop_socket(f"{msg['data']['s'].lower()}@miniTicker")
                return
        try:
            stop_loss, stop_loss_signal = get_setting()
            target = current_symbols[msg['data']['s']][2] / 100 * (100 + (stop_loss_signal * current_symbols[msg['data']['s']][3]))
        except KeyError:
            return
        if float(msg['data']['c']) > target:
            print('up!!!!')
            price_precision = int(exchange[msg['data']['s']]['pricePrecision'])
            new_stop_loss = round(current_symbols[msg['data']['s']][2] / 100 * (100 + (stop_loss * current_symbols[msg['data']['s']][3])), price_precision)
            print(f'{stop_loss} - stop-loss')
            create_order(msg['data']['s'], new_stop_loss)
            delete_order(msg['data']['s'], current_symbols[msg['data']['s']][1])
            current_symbols[msg['data']['s']][3] += 1
            current_symbols[msg['data']['s']][1] = new_stop_loss
        print(msg)

    # multiple sockets can be started
    print('!!!!!!!!!!!!!!!!!!!!!!')
    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    streams = ['bnbbtc@miniTicker']
    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    twm.join()


if __name__ == "__main__":
    main()

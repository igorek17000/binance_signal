from telethon.sync import TelegramClient
from telethon import events
import json
from binance.client import Client
from react.models import Setting, Deal
import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rest.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


def check_msg(text):
    if "#LONG" in text:
        return True
    if "#лонг" in text:
        return True
    if "#Лонг" in text:
        return True
    if "#Long" in text:
        return True
    if "#Short" in text:
        return True
    if "#SHORT" in text:
        return True
    if "#Шорт" in text:
        return True
    if "#шорт" in text:
        return True
    return False


def convert_to_dict(symbols: list):
    result_dict = {}
    for i in symbols:

        if i['symbol'] in result_dict.keys() and float(i['stopPrice']) > float(result_dict[i['symbol']]['stopPrice']):
            result_dict[i['symbol']] = i
        elif i['symbol'] not in result_dict.keys():
            result_dict[i['symbol']] = i
    return result_dict


def convert_to_dict_balance(symbols: list):
    result_dict = {}
    for i in symbols:
        result_dict[i['asset']] = i['withdrawAvailable']
    return result_dict


def get_orders():
    return convert_to_dict(client_bin.get_ticker())


def create_order(symbol, stop_price, quantity, stop_price_profit, type_pos):
    print(stop_price)
    print(stop_price_profit)
    print(quantity)
    if type_pos == 1:
        client_bin.futures_create_order(symbol=symbol,
                                        side='SELL',
                                        positionSide='BOTH',
                                        type='STOP_MARKET',
                                        closePosition='true',
                                        timeInForce='GTC',
                                        stopPrice=str(stop_price))

        client_bin.futures_create_order(symbol=symbol,
                                        side='SELL',
                                        positionSide='BOTH',
                                        type='TAKE_PROFIT_MARKET',
                                        timeInForce='GTC',
                                        stopPrice=str(stop_price_profit),
                                        closePosition='true')

        client_bin.futures_create_order(symbol=symbol,
                                        side='BUY',
                                        positionSide='BOTH',
                                        type='MARKET',
                                        quantity=str(quantity))
    else:
        client_bin.futures_create_order(symbol=symbol,
                                        side='BUY',
                                        positionSide='BOTH',
                                        type='STOP_MARKET',
                                        closePosition='true',
                                        timeInForce='GTC',
                                        stopPrice=str(stop_price))

        client_bin.futures_create_order(symbol=symbol,
                                        side='BUY',
                                        positionSide='BOTH',
                                        type='TAKE_PROFIT_MARKET',
                                        timeInForce='GTC',
                                        stopPrice=str(stop_price_profit),
                                        closePosition='true')

        client_bin.futures_create_order(symbol=symbol,
                                        side='SELL',
                                        positionSide='BOTH',
                                        type='MARKET',
                                        quantity=str(quantity))


def change_leverage(symbol: str, leverage_for_change: int):
    client_bin.futures_change_leverage(symbol=symbol,
                                       leverage=leverage_for_change)


pub = 'TmCZsJp55qJPOWgleRLsWv8VBmFq4BIBQMCy2nWQI4t48fTT7x6ums4keMXL7Azv'
pri = 'sYMXl1urFA8TlU71BvV4JeDAcs3r89bXFou2vDVDQNhudo7hW4oNJ6QNRqUb9iCG'

client_bin = Client(pub, pri)
exchange = convert_to_dict(client_bin.futures_exchange_info()['symbols'])

with open("setting.json", 'r', encoding='utf8') as out:
    setting = json.load(out)

    client = TelegramClient(
        setting['account']['session'],
        setting['account']['api_id'],
        setting['account']['api_hash']
    )

    client.start()

    dialogs = client.get_dialogs()

    for index, dialog in enumerate(dialogs):
        if index < 50:
            print(f'[{index}] {dialog.name}')

    @client.on(events.NewMessage(-1001591323415))
    async def handler_first(event):
        try:
            setting_base = Setting.objects.get(id=1)

            if setting_base.status is True:
                if check_msg(event.message.message):
                    orders = get_orders()
                    msg = event.message.message
                    type_buy = msg.split('#')[2].split("\n")[0]
                    symbol = msg.split(' ')[0].replace('/', '').replace('◾️', '').replace('#', '')

                    quantity_precision = int(exchange[symbol]['quantityPrecision'])
                    amount_precision = int(exchange[symbol]['pricePrecision'])

                    now_price = convert_to_dict(client_bin.get_ticker())[symbol]['lastPrice']
                    if type_buy == "SHORT" or type_buy == "шорт" or type_buy == "Шорт" or type_buy == "Short":
                        take_profit = round(float(now_price) / 100 * (100 - setting_base.take_profit), amount_precision)
                        stop_loss = round(float(now_price) / 100 * (100 + setting_base.stop_loss), amount_precision)
                    else:
                        take_profit = round(float(now_price) / 100 * (100 + setting_base.take_profit), amount_precision)
                        stop_loss = round(float(now_price) / 100 * (100 - setting_base.stop_loss), amount_precision)

                    change_leverage(symbol, setting_base.leverage)
                    usdt = round(
                        round(float(convert_to_dict_balance(client_bin.futures_account_balance())['USDT']), 2)
                        / 100 * setting_base.balance_percent,
                        2
                    )
                    if usdt < 6:
                        usdt = 6

                    amount = str(round(usdt / float(orders[symbol]['lastPrice']),
                                       quantity_precision))
                    if quantity_precision == 0 and float(amount) < 1:
                        amount = 1

                    if type_buy == "SHORT":
                        create_order(symbol, stop_loss, amount, take_profit, 0)
                        Deal.objects.create(coin=symbol, type='SHORT', stop_loss=stop_loss, take_profit=take_profit,
                                            leverage=setting_base.leverage)
                    elif type_buy == "LONG":
                        create_order(symbol, stop_loss, amount, take_profit, 1)
                        Deal.objects.create(coin=symbol, type='LONG', stop_loss=stop_loss, take_profit=take_profit,
                                            leverage=setting_base.leverage)
                    print('Куплено')
        except Exception as e:
            print(e)

    client.run_until_disconnected()

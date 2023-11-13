import sentry_sdk
import aiogram
import aiogram.types
import os
import asyncio
import logging
import requests
import datetime
from flask import Flask, request
from logging import handlers
from dotenv import load_dotenv
from aiogram.types import Message


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHAT_ID')
app = Flask(__name__)
bot = aiogram.Bot(token=TELEGRAM_BOT_TOKEN)
dp = aiogram.Dispatcher(bot)


# Настроить логирование
def init_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(logging.DEBUG)
    fh = logging.handlers.RotatingFileHandler(f'{name}.log')
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.info('Logger initialized')
    logger.debug('Logger initialized')
    return logger


# Flask route для обработки входящих событий
@app.route(os.getenv('WEBHOOK_ENDPOINT'), methods=['POST', 'GET'])
async def hook():
    if request.method == 'POST':
        try:
            logger.info('POST')
            print(request.json)
            message = request.json['message']
            if message == 'paymentRequestProcessAction: No free requisite found':
                host = request.json['request']['headers'][6][1]
                data_time = request.json['datetime']  # 2023-11-10T11:54:41+00:00
                # date_time преобразовать в дд:мм:гг чч:мм:сс gmt+3
                data_time = datetime.datetime.strptime(data_time, '%Y-%m-%dT%H:%M:%S+00:00')
                data_time = data_time + datetime.timedelta(hours=3)
                data_time = data_time.strftime('%d-%m-%Y %H:%M:%S')
                formatted_message = f'Нет свободных реквизитов\nЗапрос был {data_time} с хоста {host}\nтип реквизита SBER'
                try:
                    await bot.send_message(TELEGRAM_CHANNEL_ID, formatted_message)
                    logger.info(
                        f'Message sent to Telegram channel({TELEGRAM_CHANNEL_ID}):\n{formatted_message}')
                except Exception as error:
                    logger.error(f'Error sending message to Telegram channel({TELEGRAM_CHANNEL_ID}):\n{error}')
                    for i in range(3):
                        try:
                            await asyncio.sleep(60)
                            await bot.send_message(TELEGRAM_CHANNEL_ID, formatted_message)
                            logger.info(
                                f'Message sent to Telegram channel({TELEGRAM_CHANNEL_ID}):\n{formatted_message}')
                            break
                        except Exception as e:
                            logger.error(
                                f'Sending error try {str(i + 1)}. Resending message to Telegram channel({TELEGRAM_CHANNEL_ID}):{e}')
                            continue
        except Exception as error:
            logger.error(f'Error processing request:\n{error}')
            return '400'
    else:
        print('GET')
    return '200'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logger = init_logger('main')
    app.run(host="0.0.0.0", port=5000)
    print('Start')


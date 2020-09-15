# -*- coding: utf-8 -*-
import logging
import random
import sqlite3
from datetime import datetime

from flask import Flask, request
import vk_api

vk_token = os.environ["VK_TOKEN"]

"""
Пример бота для группы ВКонтакте использующего
callback-api для получения сообщений.
Подробнее: https://vk.com/dev/callback_api
Перед запуском необходимо установить flask (pip install flask)
Запуск:
$ FLASK_APP=callback_bot.py flask run
При развертывании запускать с помощью gunicorn (pip install gunicorn):
$ gunicorn callback_bot:app
"""
logger = logging.getLogger(__name__)
db = sqlite3.connect('db.db')
db.row_factory = sqlite3.Row
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS pidors (peer_id TEXT, date TEXT, screen_name TEXT, first_name TEXT)")
db.commit()


app = Flask(__name__)
vk_session = vk_api.VkApi(token=vk_token)
vk = vk_session.get_api()

confirmation_code = os.environ.get("VK_CODE")

"""
При развертывании путь к боту должен быть секретный,
поэтому поменяйте my_bot на случайную строку
Например:
756630756e645f336173313372336767
Сгенерировать строку можно через:
$ python3 -c "import secrets;print(secrets.token_hex(16))"
"""

DATE_FORMAT = "%Y-%m-%d"

def get_random_id(message_id):
    """ Get random int32 number (signed) """
    r = random.Random(message_id)
    return r.getrandbits(31) * r.choice([-1, 1])

def get_pidor(peer_id):
    cur = db.cursor()
    today = datetime.now().strftime(DATE_FORMAT)
    cur.execute("SELECT screen_name, first_name FROM pidors WHERE peer_id == ? AND date = ?", (peer_id, today))
    user = cur.fetchone()
    return user

def insert_pidor(peer_id, screen_name, first_name):
    today = datetime.now().strftime(DATE_FORMAT)
    cur.execute("INSERT INTO pidors VALUES (?, ?, ?, ?)", (peer_id, today, screen_name, first_name))
    db.commit()

@app.route('/ab4cacaee19bfd6d463096709cdadcf5', methods=['POST'])
def bot():
    # получаем данные из запроса
    data = request.get_json(force=True, silent=True)
    # ВКонтакте в своих запросах всегда отправляет поле type:
    if not data or 'type' not in data:
        return 'not ok'

    # проверяем тип пришедшего события
    if data['type'] == 'confirmation':
        # если это запрос защитного кода
        # отправляем его
        return confirmation_code
    # если же это сообщение, отвечаем пользователю
    elif data['type'] == 'message_new':
        # получаем ID пользователя
        peer_id = data['object']['message']['peer_id']
        received_text = data['object']['message']['text']
        message_id = data['object']['message']['id']
        logger.error(received_text)
        if received_text == "/pidor":
            # отправляем сообщение
            winner_db = get_pidor(peer_id)
            text_preface = "Пидор дня уже выбран. Это"
            if winner_db is None:
                users = vk.messages.getConversationMembers(peer_id=peer_id)["profiles"]
                winner = random.choice(users)
                text_preface = "Пидор дня сегодня"
            else:
                winner = winner_db

            try:
                winner_id = winner["screen_name"]
            except IndexError:
                winner_id = winner["id"]
            winner_first_name = winner["first_name"]

            if winner_db is None:
                insert_pidor(peer_id, winner_id, winner_first_name)

            text = f"{text_preface} @{winner_id} ({winner_first_name})."
            vk.messages.send(
                message=text,
                random_id=get_random_id(message_id),
                peer_id=peer_id
            )
        # возвращаем серверу VK "ok" и код 200
        return 'ok'

    return 'ok'  # игнорируем другие типы

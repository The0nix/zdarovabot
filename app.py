# -*- coding: utf-8 -*-
import os
import logging
import sqlite3

from flask import Flask, request

from bot import VKBot
import handlers

"""
Запуск:
$ FLASK_APP=callback_bot.py flask run
При развертывании запускать с помощью gunicorn (pip install gunicorn):
$ gunicorn callback_bot:app
"""
logging.basicConfig(level=logging.INFO,
                    format="[%(levelname)s] %(asctime)s: %(message)s",
                    datefmt="%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
db = sqlite3.connect("db.db")
db.row_factory = sqlite3.Row
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS pidors (peer_id TEXT, date TEXT, screen_name TEXT, first_name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS reposts (link TEXT, peer_id TEXT, time TEXT, screen_name TEXT, "
            "first_name TEXT, message TEXT)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_peer_id_link ON reposts (peer_id, link)")
db.commit()


def create_app():
    app = Flask(__name__)
    # existing code omitted

    import db
    db.init_app(app)

    return app


app = create_app()
bot = VKBot(os.environ["VK_TOKEN"], os.environ["VK_CODE"])
bot.add_handler(handlers.play_pidor_handler)
bot.add_handler(handlers.pidor_stats_handler)
bot.add_handler(handlers.shame_repost_handler)


@app.route("/ab4cacaee19bfd6d463096709cdadcab", methods=["POST"])
def main():
    data = request.get_json(force=True, silent=True)
    return bot.handle(data)

import random
import logging
from datetime import datetime
from db import get_db

from bot import Handler

logger = logging.getLogger(__name__)


DATE_FORMAT = "%Y-%m-%d"


def get_random_id(message_id):
    """ Get random int32 number (signed) """
    r = random.Random(message_id)
    return r.getrandbits(31) * r.choice([-1, 1])


def get_pidor(peer_id):
    db = get_db()
    cur = db.cursor()
    today = datetime.now().strftime(DATE_FORMAT)
    cur.execute("SELECT screen_name, first_name FROM pidors WHERE peer_id == ? AND date = ?", (peer_id, today))
    user = cur.fetchone()
    return user


def insert_pidor(peer_id, screen_name, first_name):
    db = get_db()
    cur = db.cursor()
    today = datetime.now().strftime(DATE_FORMAT)
    cur.execute("INSERT INTO pidors VALUES (?, ?, ?, ?)", (peer_id, today, screen_name, first_name))
    db.commit()


def get_pidor_stats(peer_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT first_name, screen_name, COUNT(*) \"count\" FROM pidors WHERE peer_id == ? GROUP BY screen_name",
                (peer_id,))
    stats = cur.fetchall()
    return stats


def play_pidor_callback(data, vk):
    peer_id = data['object']['message']['peer_id']
    message_id = data['object']['message']['id']
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


def pidor_stats_callback(data, vk):
    peer_id = data['object']['message']['peer_id']
    message_id = data['object']['message']['id']
    stats = sorted(get_pidor_stats(peer_id), key=lambda x: x[-1], reverse=True)
    pidors_text = "\n".join(f"{n}. {first_name} ({screen_name}) - {count}"
                            for n, (first_name, screen_name, count) in enumerate(stats, 1))
    text = f"Топ пидоров:\n{pidors_text}"
    vk.messages.send(
        message=text,
        random_id=get_random_id(message_id),
        peer_id=peer_id
    )


play_pidor_handler = Handler("^/pidor$", play_pidor_callback)
pidor_stats_handler = Handler("^/pidorstats$", pidor_stats_callback)

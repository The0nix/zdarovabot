import re
import random
import logging
from dataclasses import dataclass
from datetime import datetime

from db import get_db
from bot import Handler

logger = logging.getLogger(__name__)


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LINK_REGEX = re.compile(r"(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))")

SHAME_TEXTS = [
    "Чё за баян нах?",
    "Ты чё офигел баяны свои кидать?",
    "Ну-ка унеси свой баян нафиг отсюда.",
    "Так-с так-с так-с, что тут у нас? Опять баян притащил.",
    "Быыыыылооооо.",
    "Было.",
    "Да кидали уже!",
    "Всё ок? Это уже было.",
    "Если чё, это уже кидали",
]

### ---- Helper functions and classes ---- ###

@dataclass
class Repost:
    time: datetime
    first_name: str
    message: str


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


def get_repost(peer_id, link):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT time, first_name, message FROM REPOSTS WHERE peer_id = ? AND link = ?", (peer_id, link))
    repost = cur.fetchone()
    if repost is None:
        return None
    return Repost(time=datetime.strptime(repost["time"], DATETIME_FORMAT),
                  first_name=repost["first_name"], message=repost["message"])


def strip_link(link):
    link = link.replace("https://", "")
    link = link.replace("http://", "")
    link = link.strip("/")
    return link


def add_link(link, peer_id, time, screen_name, first_name, message):
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO reposts (link, peer_id, time, screen_name, first_name, message)"
                "VALUES (?, ?, ?, ?, ?, ?)",
                (link, peer_id, time.strftime(DATETIME_FORMAT), screen_name, first_name, message))
    db.commit()


### ---- Callbacks ---- ###
def play_pidor_callback(data, vk):
    peer_id = data["object"]["message"]["peer_id"]
    message_id = data["object"]["message"]["id"]
    logger.error(message_id)
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
        peer_id=peer_id,
        reply_to=message_id,
    )


def pidor_stats_callback(data, vk):
    peer_id = data["object"]["message"]["peer_id"]
    message_id = data["object"]["message"]["id"]
    stats = sorted(get_pidor_stats(peer_id), key=lambda x: x[-1], reverse=True)
    pidors_text = "\n".join(f"{n}. {first_name} ({screen_name}) - {count}"
                            for n, (first_name, screen_name, count) in enumerate(stats, 1))
    text = f"Топ пидоров:\n{pidors_text}"
    vk.messages.send(
        message=text,
        random_id=get_random_id(message_id),
        peer_id=peer_id,
        reply_to=message_id,
    )


def shame_repost_callback(data, vk):
    peer_id = data["object"]["message"]["peer_id"]
    message_id = data["object"]["message"]["id"]
    links = re.findall(LINK_REGEX, data["object"]["message"]["text"])
    for link in links:
        link = strip_link(link)
        repost = get_repost(peer_id, link)
        if repost is not None:
            shame_text = random.choice(SHAME_TEXTS)
            info_text = f"{repost.first_name} уже присылал " \
                        f"это {repost.time.strftime('%d.%m.%Y')} " \
                        f"в {repost.time.strftime('%H:%M:%S')}:\n\"{repost.message}\""
            text = "\n".join([shame_text, info_text])
            vk.messages.send(
                message=text,
                random_id=get_random_id(message_id),
                peer_id=peer_id,
            )
        else:
            message = data["object"]["message"]
            user = vk.users.get(user_ids=[message["from_id"]])[0]
            add_link(link=link, peer_id=message["peer_id"], time=datetime.fromtimestamp(message["date"]),
                     screen_name=user["id"], first_name=user["first_name"], message=message["text"])


play_pidor_handler = Handler("^/pidor$", play_pidor_callback)
pidor_stats_handler = Handler("^/pidorstats$", pidor_stats_callback)
shame_repost_handler = Handler(LINK_REGEX, shame_repost_callback)

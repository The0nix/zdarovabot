import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Pattern, Union, Any

import vk_api


@dataclass
class Handler:
    regex: Union[Pattern, str]
    callback: Callable[[Optional[Dict], Any], None]


class VKBot:
    def __init__(self, token: str, confirmation_code) -> None:
        vk_session = vk_api.VkApi(token=token)
        self.vk = vk_session.get_api()
        self.handlers = []
        self.confirmation_code = confirmation_code

    def add_handler(self, handler: Handler):
        self.handlers.append(handler)

    def handle(self, data: Optional[Dict]) -> str:
        if not data or 'type' not in data:
            return 'not ok'

        if data['type'] == 'confirmation':
            return self.confirmation_code

        elif data['type'] == 'message_new':
            for handler in self.handlers:
                if re.match(handler.regex, data['object']['message']['text']):
                    handler.callback(data, self.vk)
                    break
            return "ok"
        return "ok"

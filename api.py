import json
import requests

class TelegramBot:
  """Telegram bot api wrapper
  :usage:
  bot = TelegramBot(token, chat_id)
  bot.send_message("This is a TEST")
  bot.send_photo("TEST.png")
  """
  host = "https://api.telegram.org"

  def __init__(self, token=None, chat_id=None):
    self.token = token
    if chat_id is None:
      self.set_chat_id()
    else:
      self.chat_id = chat_id

  def _api_getter(self, host, url, params):
    json_response = requests.get((host + url + "?"), params=params)
    dict_response = json.loads(json_response.content)
    return dict_response.get('result', {})

  def _api_poster(self, host, url, files, params):
    json_response = requests.post((host + url), files=files, params=params)
    dict_response = json.loads(json_response.content)
    return dict_response.get('result', {})

  def get_updates(self):
    url = f"/bot{self.token}/getUpdates"
    return self._api_getter(self.host, url, None)

  def get_chat_id(self, index=0):
    chat_ids = self.get_updates()
    assert len(chat_ids) > 0, "No chat id found"
    return chat_ids[index]['my_chat_member']['chat']['id']

  def set_chat_id(self, index=0):
    self.chat_id = self.get_chat_id(index)

  def send_message(self, text, chat_id=None):
    chat_id = chat_id if chat_id is not None else self.chat_id
    url = f"/bot{self.token}/sendMessage"
    params = {'chat_id': chat_id, 'text': text}
    return self._api_getter(self.host, url, params)

  def send_message_chunk(self, text, chat_id=None, chunk_size=4096):
    messages = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    for i, msg in enumerate(messages):
      self.send_message(msg, chat_id)

  def send_photo(self, path_img, chat_id=None):
    chat_id = chat_id if chat_id is not None else self.chat_id
    url = f"/bot{self.token}/sendPhoto"
    files = {'photo': open(path_img, 'rb')}
    params = {'chat_id': chat_id}
    return self._api_poster(self.host, url, files, params)

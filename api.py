from datetime import datetime
import json
import numpy as np
import pandas as pd
import pytz
import requests
import time

class BlackScholes:
  from scipy.stats import norm
  Nc = norm.cdf
  Np = norm.pdf

  def __init__(self, S=None, K=None, T=None, R=None, sigma=None):
    """
    :param S: the price of the underlying asset at time t
    :param K: the strike price of the option, also known as the exercise price
    :param T: the time of option expiration
    :param R: the annualized risk-free interest rate, continuously compounded
    :param sigma: the standard deviation of the stock's returns, a measure of its volatility
    """
    self.S = S
    self.K = K
    self.T = T
    self.R = R
    self.sigma = sigma

  def price(self, S, K, T, R, sigma, option_type):
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "C":
      price = S * self.Nc(d1) - K * np.exp(-R*T)* self.Nc(d2)
    elif option_type == "P":
      price = K * np.exp(-R*T) * self.Nc(-d2) - S * self.Nc(-d1)
    return price

  def delta(self, S, K, T, R, sigma, option_type):
    """
    :return: float, p(V)/p(S), p: partial differential, V(S,t): option price
    """
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    if option_type == "C":
      delta = self.Nc(d1)
    elif option_type == "P":
      delta = self.Nc(d1) - 1
    return delta

  def gamma(self, S, K, T, R, sigma):
    """
    :return: float, p^2(V)/p^2(S), p: partial differential, V(S,t): option price
    """
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    gamma = self.Np(d1) / (S * sigma * np.sqrt(T))
    return gamma

  def vega(self, S, K, T, R, sigma):
    """
    :return: float, p(V)/p(sigma), p: partial differential, V(S,t): option price
    """
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    vega = S * self.Np(d1) * np.sqrt(T)
    return vega * 0.01

  def theta(self, S, K, T, R, sigma, option_type):
    """
    :return: float, p(V)/p(t), p: partial differential, V(S,t): option price
    """
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "C":
      theta = -S * self.Np(d1) * sigma / (2 * np.sqrt(T)) - R * K * np.exp(-R * T) * self.Nc(d2)
    elif option_type == "P":
      theta = -S * self.Np(d1) * sigma / (2 * np.sqrt(T)) + R * K * np.exp(-R * T) * self.Nc(-d2)
    return theta / 365

  def rho(self, S, K, T, R, sigma, option_type):
    """
    :return: float, p(V)/p(R), p: partial differential, V(S,t): option price
    """
    d1 = (np.log(S / K) + (R + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "C":
      rho = K * T * np.exp(-R * T) * self.Nc(d2)
    elif option_type == "P":
      rho = -K * T * np.exp(-R * T) * self.Nc(-d2)
    return rho * 0.01

  def option_value_expiry(self, S, K, size, option_type):
    """
    :return: float, the intrinsic value in dollars at expiry of a linear options
    """
    if option_type == "C":
      option_value = max(0, S - K) * size
    elif option_type == "P":
      option_value = max(0, K - S) * size
    return option_value

class DataToolKits:
  def __init__(self, **kwargs):
    pass

  def _datetime_to_timestamp(self, dt):
    """
    :param dt: Datetime
    :return: int, Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)

  def _timestamp_to_datetime(self, timestamp_ms):
    """
    :param timestamp_ms: int, Unix timestamp in milliseconds
    :return: datetime
    """
    timestamp_s = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_s)

  def _timestamp_to_fmtstr(self, timestamp_ms, format='%Y-%m-%d %H:%M %Z%z', time_zone=None):
    """
    :param timestamp_ms: int, Unix timestamp in milliseconds
    :param format: str, datetime format
    :param time_zone: str, timezone
    :return: str, formatted datetime-string
    """
    if time_zone is not None:
      tz = pytz.timezone(time_zone)
      dt_obj = self._timestamp_to_datetime(timestamp_ms).astimezone(tz)
    else:
      dt_obj = self._timestamp_to_datetime(timestamp_ms)
    return dt_obj.strftime(format)

  def _df_splits_instrument_components(self, df):
    """
    :param df: pandas.DataFrame, with instrument_name column in the format BTC-21MAR25-100000-C
    :return: pandas.DataFrame, with the instrument_name column been splitted into separate columns
    """
    # Split the instrument name into separate columns and merge back to the dataframe
    instrument_components = df['instrument_name'].str.split("-", expand=True)
    instrument_components.columns = ['underlying', 'maturity', 'strike', 'op_type']
    # Convert maturity to datetime and strike to integer
    instrument_components['maturity'] = pd.to_datetime(instrument_components['maturity'])
    instrument_components['strike'] = instrument_components['strike'].astype(float)
    # Merge the split instrument components back into the original dataframe
    return pd.concat([df, instrument_components], axis=1)

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

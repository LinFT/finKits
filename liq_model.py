import numpy as np

class LiquidityEstimator:
  """
  :usage:
  liq_est = LiquidityEstimator()
  ar_ests = liq_est.abdi_ranaldo_estimator_window(df.high.values, df.low.values, df.close.values, 15)
  cs_ests = liq_est.corwin_schultz_estimator_window(df.high.values, df.low.values, 15)
  """
  TOL = 1e-9 # TOL is considered as zero

  def abdi_ranaldo_estimator(self, highs, lows, closes):
    """The Abdi and Ranaldo (2017) estimator (AR_t),
    which is one of the transactions-based liquidity estimator for each interval t.
    Ref: Abdi, F., Ranaldo, A., 2017. "A simple estimation of bid-ask spreads from daily close, high and low prices" Rev. Financ. Stud.
    :param highs: list, np.array, high prices of certain timeframe
    :param lows: list, np.array, low prices of certain timeframe
    :param closes: list, np.array, close prices of certain timeframe
    :return: float
    """
    log_highs, log_lows, log_closes = np.log(highs), np.log(lows), np.log(closes)
    # Calculate midpoint between high and low log prices
    beta = (log_highs + log_lows) / 2
    # AR_i: Use the‘two-day corrected’ version of the estimator,
    # which uses high and low price data from two adjacent subintervals i and i+1
    AR_i = 4*(log_closes[:-1] - beta[:-1]) * (log_closes[:-1] - beta[1:])
    AR_i = np.sqrt(np.maximum(AR_i, 0))
    AR_t = np.mean(AR_i) if len(AR_i) > 0 else 0
    return AR_t

  def abdi_ranaldo_estimator_window(self, highs, lows, closes, window):
    """The Abdi and Ranaldo (2017) estimator (AR_t) with rolling window
    :param highs: list, np.array, high prices of certain timeframe
    :param lows: list, np.array, low prices of certain timeframe
    :param closes: list, np.array, close prices of certain timeframe
    :param window: int, the calculated AR_ests = AR_t1, AR_t2, ..., where t1=t_0~t_window-1, t2=t_1~t_window, ...
    :return: np.array, length = input-data-length, with window-1 NaN values at the start
    """
    if not (len(highs) == len(lows) == len(closes)):
      raise ValueError("Input arrays must have the same shape")
    if window <= 0:
      raise ValueError("Window size must be a positive integer")
    n_ts = len(highs)
    if n_ts <= window: # Handling cases of incomplete data
        return [np.nan] * n_ts
    AR_ests = []
    for i in range(n_ts - window + 1):
      window_highs, window_lows, window_closes = highs[i:i+window], lows[i:i+window], closes[i:i+window]
      AR_ests.append(self.abdi_ranaldo_estimator(window_highs, window_lows, window_closes))
    # Padding NaN values at the start of the sequence to ensure consistent lengths
    padding = [np.nan] * (window-1)
    return np.array(padding + AR_ests)

  def corwin_schultz_estimator(self, highs, lows):
    """The Corwin and Schultz (2012) estimator (CS_t),
    which is one of the transactions-based liquidity estimator for each interval t.
    Ref: Corwin, S.A., Schultz, P., 2012 "A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices" J. Finance
    :param highs: list, np.array, high prices of certain timeframe
    :param lows: list, np.array, low prices of certain timeframe
    :return: float
    """
    # The CS estimator is calculated from the high/low prices of two adjacent subintervals i, i+1
    highs = np.array(highs)
    lows = np.array(lows) + self.TOL
    # high_adjs/low_adjs refer to the high/low price, of two adjacent subintervals i, i+1
    high_adjs = np.maximum(highs[:-1], highs[1:])
    low_adjs = np.minimum(lows[:-1], lows[1:]) + self.TOL
    beta = (np.log(highs[:-1] / lows[:-1])**2 + np.log(highs[1:] / lows[1:])**2)
    gamma = np.log((high_adjs / low_adjs))**2
    d0 = 3 - 2*2**.5
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta))/d0 - np.sqrt(gamma / d0)
    # Finally get CS_i,i+1:
    CS_adjs = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    # Set negative values of the proxy to zero
    CS_adjs = np.where(CS_adjs < 0, 0, CS_adjs)
    # CS_t for period t is the unweighted average of all CS-estimators for adjacent subintervals in t
    CS_t = np.nanmean(CS_adjs)
    return CS_t

  def corwin_schultz_estimator_window(self, highs, lows, window):
    """The Corwin and Schultz (2012) estimator (CS_t) with rolling window
    :param highs: list, np.array, high prices of certain timeframe
    :param lows: list, np.array, low prices of certain timeframe
    :param window: int, the calculated CS_ests = CS_t1, CS_t2, ..., where t1=t_0~t_window-1, t2=t_1~t_window, ...
    :return: np.array, length = input-data-length, with window-1 NaN values at the start
    """
    if not (len(highs) == len(lows)):
      raise ValueError("Input arrays must have the same shape")
    if window <= 0:
      raise ValueError("Window size must be a positive integer")
    n_ts = len(highs)
    if n_ts <= window: # Handling cases of incomplete data
      return [np.nan] * n_ts
    CS_ests = []
    for i in range(n_ts - window + 1):
      window_highs, window_lows = highs[i:i+window], lows[i:i+window]
      CS_ests.append(self.corwin_schultz_estimator(window_highs, window_lows))
    # Padding NaN values at the start of the sequence to ensure consistent lengths
    padding = [np.nan] * (window-1)
    return np.array(padding + CS_ests)


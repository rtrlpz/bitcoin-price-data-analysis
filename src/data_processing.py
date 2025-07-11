import os
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from ta.momentum import  RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands


def load_bitcoin_data(file_name='bitcoin_historical_price_daily.csv', data_folder='raw'):
    """
    Load Bitcoin historical data from a CSV file.
    This function assumes that it's on a folder called 'raw'.
    This functions assume that the folder 'raw' is inside another folder called 'data'.
    :param file_name: Name of the CSV file to get the data from.
    :param data_folder: Data folder where the CSV is.
    :return: A data frame containing bitcoin historical data from a CSV file stored locally.
    """
    # Determine root directory path dynamically
    # This assumes that this file is in the src/ folder and the root is one level up from src/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(project_root, 'data', data_folder, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_name}' was not found in '{file_path}'."
                                "Make sure to have run the 01_data_extraction.ipynb first.")

    df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    # Delete unwanted columns
    df = df.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')
    df.index = pd.to_datetime(df.index).tz_localize(None)  # Removing UTC

    return df

def calculate_returns(df, price_col='Close'):
    """
    Calculates daily returns simple and logarithms for one price column.
    :param df: Dataframe that will be used by this function.
    :param price_col: Price column used to calculate returns.
    :return: Returns simples and logarithms returns columns.
    """
    df['Simple_Returns'] = df[price_col].pct_change()
    df['Log_Returns'] = np.log(df[price_col] / df[price_col].shift(1))

    return df

def calculate_moving_averages(df, price_col='Close', windows=None):
    """
    Calculates moving averages (SMA) and exponential averages (EMA).
    :param df: Dataframe that will be used by this function.
    :param price_col: Price column used to calculate returns.
    :param windows: Amount of days that should be used to calculate each indicator.
    :return: Two columns that have the SMA and EMA calculated.
    """
    # Assign default values when none have been provided
    if windows is None:
        windows = [20, 50, 200]
    # Calculate the SMA and EMA dynamically
    for window in windows:
        df[f'SMA_{window}'] = df[price_col].rolling(window=window).mean()
        df[f'EMA_{window}'] = df[price_col].ewm(span=window, adjust=False).mean()

    return df

def calculate_volatility(df, returns_col='Log_Returns', window=20):
    """
    Calculates daily and annual volatility based on the 252 days of trading.
    Also calculates the range, High-Low
    :param df:
    :param returns_col:
    :param window:
    :return:
    """
    df[f'Daily_Volatility_{window}D'] = df[returns_col].rolling(window=window).std()
    df[f'Annualized_Volatility_{window}D'] = df[f'Daily_Volatility_{window}D'] * np.sqrt(252)
    df[f'High_Low_Range'] = df['High'] - df['Low']
    df[f'High_Low_Percentage_Range'] = (df['High'] - df['Low']) / df['Close']

    return df

def calculate_rsi(df, price_col='Close', window=14):
    """
    Calculates the RSI - Relative Strength Index
    :param df:
    :param price_col:
    :param window:
    :return:
    """
    df['RSI'] = RSIIndicator(close=df[price_col], window=window).rsi()

    return df

def calculate_macd(df, price_col='Close', window_fast=12, window_slow=26, window_sign=9):
    """

    :param df:
    :param price_col:
    :param window_fast:
    :param window_slow:
    :param window_sign:
    :return:
    """
    macd_indicator = MACD(close=df[price_col], window_fast=window_fast,
                          window_slow=window_slow, window_sign=window_sign)

    df['MACD_Line'] = macd_indicator.macd()
    df['MACD_Signal_Line'] = macd_indicator.macd_signal()
    df['MACD_Histogram'] = macd_indicator.macd_diff()

    return df

def calculate_bollinger_bands(df, price_col='Close', window=20, window_dev=2):
    """

    :param df:
    :param price_col:
    :param window:
    :param window_dev:
    :return:
    """
    bollinger_indicator = BollingerBands(close=df[price_col], window=window, window_dev=window_dev)

    df['Bollinger_Bands_Middle'] = bollinger_indicator.bollinger_mavg()
    df['Bollinger_Bands_Upper'] = bollinger_indicator.bollinger_hband()
    df['Bollinger_Bands_Lower'] = bollinger_indicator.bollinger_lband()
    df['Bollinger_Bands_Width'] = bollinger_indicator.bollinger_wband()

    return df

def create_lagged_features(df, columns_to_lag=None, lags=None):
    """

    :param df:
    :param columns_to_lag:
    :param lags:
    :return:
    """
    if columns_to_lag is None:
        columns_to_lag = ['Close', 'Volume', 'High', 'Low']
    if lags is None:
        lags = [1, 7]

    for col in columns_to_lag:
        for lag in lags:
            df[f'{col}_Lag_{lag}'] = df[col].shift(lag)
    return df

def create_event_features(df: pd.DataFrame):
    """
    Create binary columns for important events of bitcoin.
    :param df: asdf
    :return:asdf
    """
    df['Halving_Event'] = 0

    # Aproximate dates for bitcoin halvings events (UTC)
    # Add more events in string format 'YYYY-MM-DD'
    halving_dates = [
        '2012-11-28',
        '2016-07-09',
        '2020-05-11',
        '2024-04-19'
    ]

    for date_str in halving_dates:
        # Mark the date of the event as 1
        if date_str in df.index:
            df.loc[date_str, 'Halving_Event'] = 1
        else:
            # If exact date not found, try find the closest date
            # (e.g., if data is daily close, it might be the next day's open
            # This is a robust way to find the actual market day if the exact date is a weekend/holiday
            try:
                closest_idx = df.index.get_indexer([pd.to_datetime(date_str)], method='nearest')[0]
                closest_date = df.index[closest_idx]
                df.loc[closest_date, 'Halving_Event'] = 1
                # print(f"Warning: Exact halvind date {date_str} not found in index and no nearest date found")
            except KeyError:
                print(f"Warning: Halving date {date_str} not found in index and no nearest date found.")

    return df

def run_adfuller_test(series, name="Series"):
    """
    Run the ADF Test and show the results.
    :param series:
    :param name:
    :return:
    """
    print(f"\n--- ADF Test Results for: {name} ---")

    result = adfuller(series.dropna(), autolag='AIC')
    labels = ['ADF Statistics', 'p-value', '#Lags Used', 'Number of Observations Used']

    for value, label in zip(result, labels):
        print(f'{label}: {value}')
    if result[1] <= 0.05:
        print("Conclusion: Null (H0)  Hypothesis REJECTED. The series IS STATIONARY (or it doesn't have a unitary root.")

    else:
        print("Conclusion: Null (H0) Hypothesis NOT REJECTED. The series is NOT STATIONARY (or it does have a unitary root.")

    print("\nADF test completed.")
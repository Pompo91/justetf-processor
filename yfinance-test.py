import yfinance as yf
import pandas as pd
import numpy as np
import json

def filter_history(full_history: pd.DataFrame) -> pd.DataFrame:
    dates = np.array(full_history["Close"].index)

    # convert to UTC timezone and round it to hours
    utc_dates = list()
    secs_in_12hours = 12 * 60 * 60
    secs_in_24hours = 2 * secs_in_12hours
    for d in dates:
        d_utc = np.datetime64(d, 's')     # Convert to seconds precision - also converts the timezone?
        if (d_utc.astype(np.int64) % secs_in_24hours > secs_in_12hours):
            # do the rounding
            d_utc += np.timedelta64(secs_in_12hours, 's')
        utc_dates.append(d_utc.astype('datetime64[D]'))

    data = pd.DataFrame(data = {"values": full_history["Close"].values}, index = pd.DatetimeIndex(utc_dates))
    
    # BIG TODO: filling in the missing days - I think we don't want that for correlation measurements, do we?
    # Maybe it's better idea to keep it? As the data may come from different stock exchanges in different time
    # zones etc., so after conversion to UTC, for one exchange the data are on Monday-Friday, while for another one
    # it would be Tuesday-Saturday. And some exchanges may be closed on some local public holidays, while others
    # stay open...
    # Also, what does the filling of weekends with the latest value do? It will probably increase the correlation,
    # which is not as bad as if it would be decreasing it...
    full_date_range = pd.date_range(start = utc_dates[0], end = utc_dates[-1])
    data = data.reindex(full_date_range)
    data.ffill(inplace = True)

    return data

class YfinanceData:
    _name: str
    _ticker: yf.Ticker
    _data: pd.DataFrame
    _history_close: pd.DataFrame
    _currency: str

    def __init__(self, ticker_name: str):
        self._name = ticker_name
        self._ticker = yf.Ticker(ticker_name)
        self._data = filter_history(self._ticker.history(period = "max"))
        self._currency = self._ticker.get_info()["currency"]
    
    def generate_json(self, tgt_currency: str, tgt_currency_ticker: yf.Ticker, json_path: str):
        if self._currency != tgt_currency:
            currency_history = filter_history(tgt_currency_ticker.history(period = "max"))
            history = multiply_histories(self._data, currency_history)
        else:
            history = self._data
            print("Currencies match, no need for conversion.")
        
        # history = fill_empty_days(history)
        history = convert_to_percentage(history)

        out_json = dict()
        out_json["series"] = list()

        for index, row in history.iterrows():
            point = dict()
            point["date"] = pd.to_datetime(index).strftime("%Y-%m-%d")
            point["value"] = dict()
            point["value"]["raw"] = row["values"]
            out_json["series"].append(point)
        
        with open("converted-yfinance/{}.json".format(json_path), "w") as f:
            f.write(json.dumps(out_json, indent = 2))
            


def multiply_histories(history1: pd.DataFrame, history2: pd.DataFrame) -> pd.DataFrame:
    # TODO: modify the dates, so they only contain days, no smaller values
    merged_df = pd.merge(history1, history2, left_index = True, right_index = True, suffixes = ("_h1", "_h2"))
    merged_df["values"] = merged_df["values_h1"] * merged_df["values_h2"]
    return merged_df[["values"]]

"""
def fill_empty_days(data: pd.DataFrame) -> pd.DataFrame:
    full_date_range = pd.date_range(start = data["datetime"].iloc[0], end = data["datetime"].iloc[-1])
    data.set_index("datetime")
    data.reindex(full_date_range)
    data["values"] = data["values"].fillna(method = "ffill")
    return data
"""

def convert_to_percentage(data: pd.DataFrame):
    base = data["values"].iat[0]
    data["values"] = (data["values"] / base - 1) * 100
    return data

"""
def get_start_stop_idx(dates: pd.DatetimeIndex, min_date: np.datetime64, max_date: np.datetime64) -> (int, int):
    start_idx = None
    stop_idx = None
    for i, d in enumerate(dates):
        if d == min_date:
            start_idx = i
            break
    
    for i, d in reversed(list(enumerate(dates))):
        if d == max_date:
            stop_idx = len(dates) - i
            break
    
    assert (start_idx != None and stop_idx != None)
    return (start_idx, stop_idx)
"""

"""
# return list of dicts
def fill_empty_days_relative(values: list, dates: pd.DatetimeIndex) -> list:
    day_dates = np.array(dates, dtype = 'datetime64[D]')
    assert(len(values) == len(day_dates))

    out_values = list([values[0]])
    # these are np.datetime - will be converted to strings at the end
    out_dates = list([day_dates[0]])

    for i in range(len(values) - 1):
        while out_dates[-1] + np.timedelta64(1, 'D') != day_dates[i]:
            out_dates.append(out_dates[-1] + np.timedelta64(1, 'D'))
            # dirty, but efficient - do the conversion to performance in % here
            out_values.append((out_values[-1] - out_values[0]) / out_values[0] * 100)

    out_dict_list = list()

    for i in range(len(out_dates)):
        p = dict()
        p["date"] = pd.to_datetime(out_dates[i]).strftime("%Y-%m-%d")
        p["value"] = dict()
        p["value"]["raw"] = out_values[i]
        out_dict_list.append(p)
    
    return out_dict_list
"""



currency = yf.Ticker("EUR=X")

for ticker in [("SP500", "SPY"), ("amundi-semi", "CHIP.SW"), ("msci-health", "LYPE.DE"), ("msci-india", "LYMD.DE"), ("euro-estate", "XDER.L")]:
    data = YfinanceData(ticker[1])
    data.generate_json("EUR", currency, ticker[0])
    # if ticker.get_info().cur
    # ticker.get_info
    # ticker.to_pickle("yfinance-pickles/{}-ticker.pkl")
    # history.to_json("yfinance-jsons/{}.json".format(t[0]))
    b = 1
#usd_eur = yf.Ticker("EUR=X")

a = 1
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
    _currency: str

    def __init__(self, ticker_name: str):
        self._name = ticker_name
        self._ticker = yf.Ticker(ticker_name)
        self._data = filter_history(self._ticker.history(period = "max"))
        self._currency = self._ticker.get_info()["currency"].upper()
    
    def get_currency(self) -> str:
        return self._currency

    def get_data(self) -> pd.DataFrame:
        return self._data        
    
    def generate_json(self, tgt_currency: str, forex_pairs: list, json_path: str):
        if self._currency != tgt_currency:
            forex_p = None
            for p in forex_pairs:
                if p.get_conv_currency() == self._currency:
                    assert(p.get_currency() == tgt_currency)
                    forex_p = p
                    break
            if not forex_p:
                raise Exception("Forex pair for target currency {} not found.".format(tgt_currency))
            
            history = forex_p.convert_to_eur(self)
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

class ForexPair:
    # Class for holding the data used for conversion to EUR
    _name: str
    _ticker: yf.Ticker
    _data: pd.DataFrame
    _currency: str
    _conv_currency: str

    def __init__(self, ticker_name: str, conv_currency: str):
        self._name = ticker_name
        self._ticker = yf.Ticker(ticker_name)
        self._data = filter_history(self._ticker.history(period = "max"))
        self._currency = self._ticker.get_info()["currency"].upper()
        self._conv_currency = conv_currency.upper()
    
    def get_currency(self) -> str:
        return self._currency

    def get_conv_currency(self) -> str:
        assert(self._currency == "EUR")
        return self._conv_currency

    def convert_to_eur(self, data: YfinanceData) -> pd.DataFrame:
        if (data.get_currency() != self._conv_currency):
            raise Exception("Currency missmatch!")
        return multiply_histories(data.get_data(), self._data)

def multiply_histories(history1: pd.DataFrame, history2: pd.DataFrame) -> pd.DataFrame:
    # TODO: modify the dates, so they only contain days, no smaller values
    merged_df = pd.merge(history1, history2, left_index = True, right_index = True, suffixes = ("_h1", "_h2"))
    merged_df["values"] = merged_df["values_h1"] * merged_df["values_h2"]
    return merged_df[["values"]]

def convert_to_percentage(data: pd.DataFrame):
    base = data["values"].iat[0]
    data["values"] = (data["values"] / base - 1) * 100
    return data

forex_pair_list = list()
for forex_p in [("EUR=X", "USD"), ("GBPEUR=X", "GBP")]:
    forex_pair_list.append(ForexPair(forex_p[0], forex_p[1]))

for ticker in [("SP500", "SPY"), ("amundi-semi", "CHIP.PA"), ("msci-health", "LYPE.DE"), ("msci-india", "LYMD.DE"), ("euro-estate", "XDER.L")]:
    data = YfinanceData(ticker[1])
    data.generate_json("EUR", forex_pair_list, ticker[0])

a = 1
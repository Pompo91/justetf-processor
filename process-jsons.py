import json
import argparse
import datetime
from dateutil.relativedelta import relativedelta
import os

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class Series:
    _name: str
    _data: dict

    def __init__(self, json_path: str):
        try:
            self._name = json_path.split("/")[-1].split(".")[0]
            with open(json_path, "r") as f:
                whole_json = json.load(f)
                self._data = whole_json["series"]
        except:
            print("class series: exception occurred: {}".format(exc))
        
        self.__validate()
    
    def __validate(self) -> bool:
        # validate that the series has exactly one data point per day
        total_days = self.get_last_datetime() - self.get_first_datetime()
        data_points = len(self._data)

        if (total_days.days + 1) != data_points:
            raise Exception("Data series validation failed: {} days, {} data points.".format(total_days.days, data_points))

    def __get_datetime(self, date: str) -> datetime.datetime:
        return datetime.datetime.strptime(date, "%Y-%m-%d")

    def get_name(self) -> str:
        return self._name

    def get_first_datetime(self) -> datetime.datetime:
        return self.__get_datetime(self._data[0]["date"])

    def get_last_datetime(self) -> datetime.datetime:
        return self.__get_datetime(self._data[-1]["date"])

    def get_first_data(self) -> float:
        return float(self.data[0]["value"]["raw"])
    
    def get_last_data(self) -> float:
        return float(self.data[-1]["value"]["raw"])

    def write_csv(self, csv_path: str):
        with open(csv_path, "w") as f:
            f.write("date,value,\n")
            for point in self._data:
                f.write("{},{},\n".format(point["date"], point["value"]["raw"]))
    
    def get_data_in_date_window(self, start_date: datetime.datetime, stop_date: datetime.datetime) -> list:
        # Return a subset of data fitting into the defined time window, scaled to match the profits against
        # the point at start_date.
        if (start_date < self.get_first_datetime()) or (stop_date > self.get_last_datetime()):
            raise Exception("Series {}: requested dates ({}, {}) out of bounds ({}, {})".format(self._name, start_date, stop_date, self.get_first_datetime(), self.get_last_datetime()))

        first_idx = int((start_date - self.get_first_datetime()).days)
        last_idx = int((stop_date - self.get_first_datetime()).days)

        first_val = self._data[first_idx]["value"]["raw"]
        # We cannot just shift the graph by an offset of first_val - we also need to re-scale it. For that, we temporarily
        # move from percents to absolute numbers by mapping 0% profit ~ 100% of the initial value ~ abs. value 100.
        # Based on those absolute values, we're able to calculate the new profit.
        # Verified against the justETF "compare graph" - the values do match now.

        return [((100 + p["value"]["raw"]) / (100 + first_val) - 1) * 100 for p in self._data[first_idx:last_idx + 1]]

class TitleGenerator:
    _timerange_str: str

    def __init__(self, args, min_datetime: datetime, max_datetime: datetime):
        if args.months:
            self._timerange_str = "{} months".format(args.months)
        else:
            self._timerange_str = "{}/{} - {}/{}".format(min_datetime.month, min_datetime.year, max_datetime.month, max_datetime.year)

    def generate(self, main_title: str) -> str:
        return "{} ({})".format(main_title, self._timerange_str)

def generate_graph_ticks(start_date: datetime.datetime, stop_date: datetime.datetime) -> [list, list]:
    idx_list = list()
    date_str_list = list()

    year = start_date.year
    month = start_date.month
    while (month - 1) % 3 != 0:
        month += 1
        if month > 12:
            year += 1
            month = 1

    ts = datetime.datetime.strptime("1/{}/{}".format(month, year), "%d/%m/%Y")
    while ts < stop_date:
        idx_list.append(int((ts - start_date).days))
        date_str_list.append("{}/{}".format(month, year % 100))

        month = month + 3
        if month > 12:
            year += 1
            month = month % 12
        ts = datetime.datetime.strptime("1/{}/{}".format(month, year), "%d/%m/%Y")
    
    return [idx_list, date_str_list]

def generate_graphs(data: pd.DataFrame, title: str, min_datetime: datetime, max_datetime: datetime):
    # The pandas plot() function is a wrapper around the matplotlib plt.plot()
    data.plot()
    # to modify the plot, just call the method of plt

    # Set plot title and labels
    plt.title(title)
    plt.xlabel('date')

    idx_list, tick_list = generate_graph_ticks(min_datetime, max_datetime)
    plt.xticks(idx_list, tick_list, rotation = 0)

    plt.grid()
    plt.show(block = False)

def generate_corr_heatmap(corr_matrix: pd.DataFrame, title: str):
    # plt.figure()
    mask = np.triu(np.ones_like(corr_matrix, dtype = bool))
    # Add diverging colormap from red to blue
    cmap = sns.diverging_palette(250, 10, as_cmap=True)
    sns.heatmap(corr_matrix, mask = mask, vmin = -1, vmax = 1, annot = True, cmap = cmap)
    plt.title(title)
    # plt.show(block = False)

def get_linear_trend_coeffs(series: list) -> [float, float]:
    dummy_time_values = np.arange(len(series))
    # The "1" stands for "polynomial of 1st degree", i.e. linear
    return np.polyfit(dummy_time_values, series, 1)

# TODO: not used right now, but keeping it for now...
def remove_trends(data: pd.DataFrame) -> pd.DataFrame:
    tmp_dict = dict()

    for key in data.keys():
        series = list(data[key])
        tmp_dict[key] = list()
        slope, offset = get_linear_trend_coeffs(series)
        for i, p in enumerate(series):
            tmp_dict[key].append(p - (slope * i + offset))
    
    return pd.DataFrame(tmp_dict)
        
        
if __name__ == "__main__":
    arg_parser = arg_parser = argparse.ArgumentParser(description = "Process JSONSs downloaded from JustETF")
    arg_parser.add_argument("-i", "--input-json-dir", type = str, required = True, help = "Path to directory containing the JSON files")
    arg_parser.add_argument("-m", "--months", type = int, required = False, help = "Only compare the last -m months")

    args = arg_parser.parse_args()

    try:
        if not os.path.isdir(args.input_json_dir):
            raise Exception("{} is not a directory!".format(args.input_json_dir))
        
        series_list = list()
        for file in os.listdir(args.input_json_dir):
            if file.endswith(".json"):
                series_list.append(Series(os.path.join(args.input_json_dir, file)))
                print("Series \"{}\" added".format(series_list[-1].get_name()))
        
        if len(series_list) < 2:
            raise Exception("Only {} files found, at least 2 required.".format(len(series_list)))

        min_datetime = series_list[0].get_first_datetime()
        max_datetime = series_list[0].get_last_datetime()

        for s in series_list[1:]:
            min_datetime = max(min_datetime, s.get_first_datetime())
            max_datetime = min(max_datetime, s.get_last_datetime())
        
        if args.months:
            min_datetime = max_datetime - relativedelta(months = +args.months)
            for s in series_list:
                if s.get_first_datetime() > min_datetime:
                    print("Dropping series {} - starts at {}, but minimum date is {}.".format(s.get_name(), s.get_first_datetime(), min_datetime))
                    series_list.remove(s)
            if len(series_list) < 2:
                raise Exception("Only {} series remained - not enough data to compare.".format(len(series_list)))
        
        print("Min date: {}, max date: {}, days: {}".format(min_datetime, max_datetime, int((max_datetime - min_datetime).days) + 1))

        performance_dict = dict()
        abs_dict = dict()

        for s in series_list:
            subseries = s.get_data_in_date_window(min_datetime, max_datetime)
            # performance is the original graph in %, starting at 0
            performance_dict[s.get_name()] = subseries
            # for calculation of percentage change, we need absolute values
            abs_dict[s.get_name()] = [(p + 100) for p in subseries]
        
        FILTER_WINDOW = 14

        performance_dframe = pd.DataFrame(performance_dict)
        filtered_performance = performance_dframe.ewm(span = FILTER_WINDOW).mean()

        abs_dframe = pd.DataFrame(abs_dict)
        raw_pct_change = abs_dframe.pct_change()

        filtered_abs = abs_dframe.ewm(span = FILTER_WINDOW).mean()
        filtered_pct_change = filtered_abs.pct_change()
        
        # Switch to a backend that supports interactive plotting
        plt.switch_backend('TkAgg')

        title = TitleGenerator(args, min_datetime, max_datetime)

        generate_graphs(performance_dframe, title.generate("Total performance [%]"), min_datetime, max_datetime)
        generate_graphs(filtered_performance, title.generate("Filtered PERECENT, NOT ABS"), min_datetime, max_datetime)
        generate_graphs(filtered_pct_change, title.generate("Filtered pct change"), min_datetime, max_datetime)

        plt.figure()
        plt.subplots_adjust(wspace = 0.2, bottom = 0.22)
        plt.tight_layout()

        plt.subplot(1, 2, 1)
        generate_corr_heatmap(filtered_pct_change.corr(), title.generate("Correlation - filtered pct change"))
        plt.subplot(1, 2, 2)
        # TODO: maybe we don't want really "raw", but just a shorter filter window?
        generate_corr_heatmap(raw_pct_change.corr(), title.generate("Correlation - \"raw\" pct change"))
        
        # NOTE: after introducing the wspace, if we call it here again, the wspace is not set anymore...
        # now we use the fixed bottom instead - maybe we could calculate the required value based on the longest name...
        # plt.tight_layout()
        plt.show(block = False)

        input("Press Enter to terminate...")
        

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))


import json
import argparse
import datetime
import os

import seaborn as sns
import matplotlib.pyplot as plt
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
        # return a subset of data fitting into the defined time window
        if (start_date < self.get_first_datetime()) or (stop_date > self.get_last_datetime()):
            raise Exception("Series {}: requested dates ({}, {}) out of bounds ({}, {})".format(self._name, start_date, stop_date, self.get_first_datetime(), self.get_last_datetime()))

        first_idx = int((start_date - self.get_first_datetime()).days)
        last_idx = int((self.get_last_datetime() - stop_date).days)

        return [p["value"]["raw"] for p in self._data if (self.__get_datetime(p["date"]) >= start_date) and (self.__get_datetime(p["date"]) <= stop_date)]

def generate_graph_ticks(start_date: datetime.datetime, stop_date: datetime.datetime) -> [list, list]:
    idx_list = list()
    date_str_list = list()

    year = start_date.year
    month = start_date.month
    while month % 3 != 0:
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
            month = 3
        ts = datetime.datetime.strptime("1/{}/{}".format(month, year), "%d/%m/%Y")
    
    return [idx_list, date_str_list]
        

        
if __name__ == "__main__":
    arg_parser = arg_parser = argparse.ArgumentParser(description = "Process JSONSs downloaded from JustETF")
    arg_parser.add_argument("-i", "--input-json-dir", type = str, required = True, help = "Path to directory containing the JSON files")
    # arg_parser.add_argument("-o", "--output-csv", type = str, required = False, help = "Path to the output CSV file")

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
        
        print("Min date: {}, max date: {}, days: {}".format(min_datetime, max_datetime, int((max_datetime - min_datetime).days) + 1))

        subseries_list = list()
        for s in series_list:
            subseries_list.append(s.get_data_in_date_window(min_datetime, max_datetime))
        
        ######################################################################################
        # Plotting the data with a lot of help from ChatGPT...
        ######################################################################################

        # Transpose each series inside the series_list
        transposed_series = []
        for series in zip(*subseries_list):
            transposed_series.append(list(series))

        # Create a DataFrame from the transposed series
        data = pd.DataFrame(transposed_series, columns=[f'Series{i+1}' for i in range(len(subseries_list))])

        # Add X values to the DataFrame
        data['X'] = np.arange(1, len(subseries_list[0]) + 1)

        # Set up Seaborn style
        sns.set(style="whitegrid")

        # Plot each series dynamically
        for i in range(len(subseries_list)):
            sns.lineplot(x='X', y=f'Series{i+1}', data=data, label=series_list[i].get_name(), markers = False)

        # Add legend
        plt.legend()

        # Set plot title and labels
        plt.title('Dynamic Series Scatter Plot')
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')

        idx_list, tick_list = generate_graph_ticks(min_datetime, max_datetime)
        plt.xticks(idx_list, tick_list, rotation = 0)

        # Switch to a backend that supports interactive plotting
        plt.switch_backend('TkAgg')

        # Show the plot
        plt.show()

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

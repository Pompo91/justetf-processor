import json
import argparse
import datetime
import os

import matplotlib.pyplot as plt
import pandas as pd

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

def generate_graphs(data: pd.DataFrame):
    # The pandas plot() function is a wrapper around the matplotlib plt.plot()
    data.plot()
    # to modify the plot, just call the method of plt

    # Set plot title and labels
    plt.title('Performance comparison')
    plt.xlabel('date')
    plt.ylabel('performance [%]')

    idx_list, tick_list = generate_graph_ticks(min_datetime, max_datetime)
    plt.xticks(idx_list, tick_list, rotation = 0)

    plt.grid()
        
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
        dataframe_input_dict = dict()

        for s in series_list:
            subseries = s.get_data_in_date_window(min_datetime, max_datetime)
            subseries_list.append(subseries)
            dataframe_input_dict[s.get_name()] = subseries
        
        pd_data = pd.DataFrame(dataframe_input_dict)
        
        # Switch to a backend that supports interactive plotting
        plt.switch_backend('TkAgg')

        generate_graphs(pd_data)

        plt.show()

        input("Press Enter to terminate...")
        

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

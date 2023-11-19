import json
import argparse
import datetime
import os

class series:
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
                series_list.append(series(os.path.join(args.input_json_dir, file)))
                print("Series \"{}\" added".format(series_list[-1].get_name()))
        
        if len(series_list) < 2:
            raise Exception("Only {} files found, at least 2 required.".format(len(series_list)))

        min_datetime = series_list[0].get_first_datetime()
        max_datetime = series_list[0].get_last_datetime()

        for s in series_list[1:]:
            min_datetime = max(min_datetime, s.get_first_datetime())
            max_datetime = min(max_datetime, s.get_last_datetime())
        
        print("Min date: {}, max date: {}, days: {}".format(min_datetime, max_datetime, int((max_datetime - min_datetime).days) + 1))

        for s in series_list:
            subseries = s.get_data_in_date_window(min_datetime, max_datetime)
            print("Length of {} subseries: {}".format(s.get_name(), len(subseries)))

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

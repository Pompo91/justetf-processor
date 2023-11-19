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

    def __get_format_string(self) -> str:
        return "%Y-%m-%d"

    def get_name(self) -> str:
        return self._name

    def get_first_datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self._data[0]["date"], self.__get_format_string())

    def get_last_datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self._data[-1]["date"], self.__get_format_string())

    def get_first_data(self) -> float:
        return float(self.data[0]["value"]["raw"])
    
    def get_last_data(self) -> float:
        return float(self.data[-1]["value"]["raw"])

    def write_csv(self, csv_path: str):
        with open(csv_path, "w") as f:
            f.write("date,value,\n")
            for point in self._data:
                f.write("{},{},\n".format(point["date"], point["value"]["raw"]))
        
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

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

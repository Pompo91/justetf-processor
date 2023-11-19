import json
import argparse
import datetime

class series:
    _data: dict

    def __init__(self, json_path: str):
        try:
            with open(json_path, "r") as f:
                whole_json = json.load(f)
                self._data = whole_json["series"]
        except:
            print("class series: exception occurred: {}".format(exc))
        
        self.__validate()
    
    def __validate(self) -> bool:
        # validate that the series has exactly one data point per day
        format_string = "%Y-%m-%d"
        first_date = self._data[0]["date"]
        last_date = self._data[-1]["date"]
        total_days = datetime.datetime.strptime(last_date, format_string) - datetime.datetime.strptime(first_date, format_string)
        data_points = len(self._data)

        if (total_days.days + 1) != data_points:
            raise Exception("Data series validation failed: {} days, {} data points.".format(total_days.days, data_points))

    def write_csv(self, csv_path: str):
        with open(csv_path, "w") as f:
            f.write("date,value,\n")
            for point in self._data:
                f.write("{},{},\n".format(point["date"], point["value"]["raw"]))


if __name__ == "__main__":
    arg_parser = arg_parser = argparse.ArgumentParser(description = "Extract CSV from JustETF JSON response")
    arg_parser.add_argument("-i", "--input-json", type = str, required = True, help = "Path to the input JSON file")
    arg_parser.add_argument("-o", "--output-csv", type = str, required = True, help = "Path to the output CSV file")

    args = arg_parser.parse_args()

    
    whole_json = dict()

    try:
        data_series = series(args.input_json)
        data_series.write_csv(args.output_csv)

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

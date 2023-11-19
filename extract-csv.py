import json
import argparse

if __name__ == "__main__":
    arg_parser = arg_parser = argparse.ArgumentParser(description = "Extract CSV from JustETF JSON response")
    arg_parser.add_argument("-i", "--input-json", type = str, required = True, help = "Path to the input JSON file")
    arg_parser.add_argument("-o", "--output-csv", type = str, required = True, help = "Path to the output CSV file")

    args = arg_parser.parse_args()

    whole_json = dict()

    try:
        with open(args.input_json, "r") as f:
            whole_json = json.load(f)
        
        with open(args.output_csv, "w") as f:
            f.write("date,value,\n")
            for point in whole_json["series"]:
                f.write("{},{},\n".format(point["date"], point["value"]["raw"]))

    except Exception as exc:
        print("EXCEPTION OCCURRED: {}".format(exc))

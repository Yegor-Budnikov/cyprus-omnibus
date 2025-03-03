import csv
import json

def csv_to_json(csv_filename, json_filename):
    data = []
    
    with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            row["stop_sequence"] = int(row["stop_sequence"])  # Convert to int
            row["pickup_type"] = int(row["pickup_type"])  # Convert to int
            row["drop_off_type"] = int(row["drop_off_type"])  # Convert to int
            data.append(row)
    
    with open(json_filename, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    csv_to_json("stop_times.txt", "stop_times.json")

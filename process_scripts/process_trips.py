import csv
import json

def csv_to_json(csv_filename, json_filename):
    data = []
    
    with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if "stop_sequence" in row:
                row["stop_sequence"] = int(row["stop_sequence"])  # Convert to int
            if "pickup_type" in row:
                row["pickup_type"] = int(row["pickup_type"])  # Convert to int
            if "drop_off_type" in row:
                row["drop_off_type"] = int(row["drop_off_type"])  # Convert to int
            if "direction_id" in row:
                row["direction_id"] = int(row["direction_id"])  # Convert to int
            data.append(row)
    
    with open(json_filename, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    csv_to_json("trips.txt", "trips.json")

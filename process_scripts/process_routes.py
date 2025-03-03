import csv
import json

def csv_to_json(csv_filename, json_filename):
    data = []
    
    with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            data.append({
                "route_id": row["route_id"],
                "agency_id": row["agency_id"],
                "route_short_name": row["route_short_name"],
                "route_long_name": row["route_long_name"],
                "route_desc": row["route_desc"],
                "route_type": int(row["route_type"]),
                "route_color": "#" + row["route_color"],  # Fixed string concatenation
                "route_text_color": "#" + row["route_text_color"]  # Fixed string concatenation
            })
    
    with open(json_filename, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

# Example usage:
csv_filename = "routes.txt"  # Replace with your actual CSV file
json_filename = "routes.json"
csv_to_json(csv_filename, json_filename)

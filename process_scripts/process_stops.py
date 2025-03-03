import csv
import json

# Define the input and output file names
input_file = "stops.txt"  # Change to your actual file name
output_file = "stops.json"

# Read the CSV file and convert it to a JSON structure
stops = []
with open(input_file, mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        stops.append(row)

# Write the JSON output
with open(output_file, mode='w', encoding='utf-8') as file:
    json.dump(stops, file, indent=4, ensure_ascii=False)

print(f"Conversion complete! JSON saved to {output_file}")

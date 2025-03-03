import json
import requests
from flask import Flask, render_template, jsonify
from google.transit import gtfs_realtime_pb2
import pytz
import re
import csv
import os
from datetime import datetime, timedelta

app = Flask(__name__)

GTFS_REALTIME_URL = "http://20.19.98.194:8328/Api/api/gtfs-realtime"
ROUTES_FILE = "routes.json"
STOPS_FILE = "stops.json"
STOP_TIMES_FILES = ["stop_times.txt", "stop_times2.txt"] 
TRIPS_FILE = "trips.json"
CYPRUS_TZ = pytz.timezone("Asia/Nicosia")

# Load route details
try:
    with open(ROUTES_FILE, "r") as f:
        routes_data = json.load(f)

    # Ensure correct key names
    routes_dict = {
        str(route["route_id"]): {
            "route_number": route.get("route_short_name", "Unknown"),
            "route_name": route.get("route_long_name", "Unknown")
        }
        for route in routes_data
    }
except Exception as e:
    print(f"Error loading routes.json: {e}")
    routes_dict = {}


# Load bus stops
try:
    with open(STOPS_FILE, "r") as f:
        stops_data = json.load(f)
except Exception as e:
    print(f"Error loading stops.json: {e}")
    stops_data = []


# Load trips mapping
try:
    with open(TRIPS_FILE, "r") as f:
        trips_data = json.load(f)
        trips_dict = {trip["trip_id"]: {"route_id": trip["route_id"], "trip_headsign": trip["trip_headsign"]} for trip in trips_data}
except Exception as e:
    print(f"Error loading trips.json: {e}")
    trips_dict = {}


def get_scheduled_arrivals():
    """Processes stop_times.txt files to get up to 5 upcoming buses per stop, including tomorrow's first buses."""
    current_time = datetime.now(CYPRUS_TZ)  # ✅ This is timezone-aware
    stop_schedule = {}
    tomorrow_buses = {}

    time_pattern = re.compile(r"^\d{2}:\d{2}:\d{2}$")  # Ensures HH:MM:SS format

    for stop_times_file in STOP_TIMES_FILES:
        if not os.path.exists(stop_times_file):
            print(f"Warning: {stop_times_file} not found, skipping...")
            continue  # Skip if the file does not exist

        try:
            with open(stop_times_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    stop_id = row["stop_id"]
                    trip_id = row["trip_id"]
                    arrival_time = row["arrival_time"]

                    if not time_pattern.match(arrival_time):
                        print(f"Skipping invalid time format: {arrival_time}")
                        continue  # Skip invalid times

                    route_id = str(trips_dict.get(trip_id, {}).get("route_id", "Unknown"))
                    route_info = routes_dict.get(route_id, {"route_number": "Unknown", "route_name": "Unknown"})
                    route_number = route_info["route_number"]
                    route_name = route_info["route_name"]

                    schedule_entry = (arrival_time, f"{route_number} - {route_name} - {trip_id} - {arrival_time}")

                    # ✅ Convert arrival_time to timezone-aware datetime for proper sorting
                    arrival_datetime = datetime.strptime(arrival_time, "%H:%M:%S").replace(
                        year=current_time.year, month=current_time.month, day=current_time.day
                    ).astimezone(CYPRUS_TZ)  # ✅ Ensure timezone-aware

                    if arrival_datetime >= current_time:
                        if stop_id not in stop_schedule:
                            stop_schedule[stop_id] = []
                        stop_schedule[stop_id].append(schedule_entry)

                    else:  # Collect tomorrow's first buses
                        if stop_id not in tomorrow_buses:
                            tomorrow_buses[stop_id] = []
                        tomorrow_buses[stop_id].append((
                            arrival_datetime + timedelta(days=1),  # Move to next day
                            schedule_entry[1]
                        ))

        except Exception as e:
            print(f"Error reading {stop_times_file}: {e}")

    # Sort and limit to 5 results
    for stop_id in stop_schedule:
        stop_schedule[stop_id] = sorted(stop_schedule[stop_id])[:5]  # Sort by arrival_time

        # If fewer than 5 buses exist today, add first buses from tomorrow
        if len(stop_schedule[stop_id]) < 5 and stop_id in tomorrow_buses:
            tomorrow_buses[stop_id].sort()  # Sort tomorrow's buses
            stop_schedule[stop_id].extend([entry[1] for entry in tomorrow_buses[stop_id][:5 - len(stop_schedule[stop_id])]])

        stop_schedule[stop_id] = stop_schedule[stop_id][:5]  # Limit to 5 buses

    return {stop_id: [entry[1] for entry in arrivals] for stop_id, arrivals in stop_schedule.items()}

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/vehicle_positions')
def vehicle_positions():
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        response = requests.get(GTFS_REALTIME_URL)
        response.raise_for_status()
        feed.ParseFromString(response.content)

        vehicles = []
        for entity in feed.entity:
            if entity.HasField("vehicle"):
                vehicle = entity.vehicle
                route_id = vehicle.trip.route_id if vehicle.HasField("trip") else None
                route_info = routes_dict.get(route_id, {"route_short_name": "Unknown", "route_long_name": "Unknown"})

                vehicles.append({
                    "vehicle_id": vehicle.vehicle.id if vehicle.HasField("vehicle") else "Unknown",
                    "latitude": float(vehicle.position.latitude) if vehicle.HasField("position") else None,
                    "longitude": float(vehicle.position.longitude) if vehicle.HasField("position") else None,
                    "timestamp": vehicle.timestamp if vehicle.HasField("timestamp") else None,
                    "route_id": route_id,
                    "route_number": route_info["route_short_name"],
                    "route_name": route_info["route_long_name"]
                })
        
        return jsonify({"vehicles": vehicles})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GTFS data: {e}")
        return jsonify({"error": "Failed to fetch GTFS data", "details": str(e)}), 500


@app.route('/bus_stops')
def bus_stops():
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        response = requests.get(GTFS_REALTIME_URL)
        response.raise_for_status()
        feed.ParseFromString(response.content)

        trip_updates = {}
        for entity in feed.entity:
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update
                route_id = trip_update.trip.route_id
                vehicle_id = trip_update.vehicle.id if trip_update.HasField("vehicle") else "Unknown"
                route_number = routes_dict.get(route_id, {}).get("route_short_name", "Unknown")
                route_name = routes_dict.get(route_id, {}).get("route_long_name", "Unknown")

                for stop_time in trip_update.stop_time_update:
                    stop_id = stop_time.stop_id
                    arrival_time = datetime.fromtimestamp(stop_time.arrival.time, CYPRUS_TZ).strftime("%H:%M:%S") if stop_time.HasField("arrival") else "N/A"
                    
                    if stop_id in trip_updates:
                        trip_updates[stop_id].append(f"{route_number} - {route_name} - {vehicle_id} - {arrival_time}")
                    else:
                        trip_updates[stop_id] = [f"{route_number} - {route_name} - {vehicle_id} - {arrival_time}"]

        for stop in stops_data:
            stop["upcoming_buses"] = trip_updates.get(stop["stop_id"], [])
        
        return jsonify({"stops": stops_data})
    except Exception as e:
        print(f"GTFS API unavailable, falling back to stop_times.json: {e}")
        stop_schedule = get_scheduled_arrivals()
        for stop in stops_data:
            stop["upcoming_buses"] = stop_schedule.get(stop["stop_id"], [])
        return jsonify({"stops": stops_data}) 

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # Use PORT from Render
    app.run(host="0.0.0.0", port=port)
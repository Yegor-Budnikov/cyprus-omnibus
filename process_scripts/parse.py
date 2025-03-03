import json  # Import JSON for output formatting
from google.transit import gtfs_realtime_pb2  # Import GTFS-Realtime protocol buffer

def parse_gtfs_realtime(file_path):
    """Parses a GTFS-Realtime file and converts it into a full JSON structure."""
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        with open(file_path, "rb") as f:
            feed.ParseFromString(f.read())

        entities = []
        for entity in feed.entity:
            entity_data = {
                "id": entity.id,
                "is_vehicle": entity.HasField("vehicle"),
                "is_trip_update": entity.HasField("trip_update"),
                "is_alert": entity.HasField("alert")
            }
            
            if entity.HasField("vehicle"):
                vehicle = entity.vehicle
                entity_data["vehicle"] = {
                    "vehicle_id": vehicle.vehicle.id if vehicle.HasField("vehicle") else "Unknown",
                    "latitude": vehicle.position.latitude if vehicle.HasField("position") else None,
                    "longitude": vehicle.position.longitude if vehicle.HasField("position") else None,
                    "timestamp": vehicle.timestamp if vehicle.HasField("timestamp") else None,
                    "trip_id": vehicle.trip.trip_id if vehicle.HasField("trip") else None,
                    "route_id": vehicle.trip.route_id if vehicle.HasField("trip") else None
                }
            
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update
                entity_data["trip_update"] = {
                    "trip_id": trip_update.trip.trip_id,
                    "route_id": trip_update.trip.route_id,
                    "stop_time_updates": [
                        {
                            "stop_id": update.stop_id,
                            "arrival_time": update.arrival.time if update.HasField("arrival") else None,
                            "departure_time": update.departure.time if update.HasField("departure") else None
                        }
                        for update in trip_update.stop_time_update
                    ]
                }
            
            if entity.HasField("alert"):
                alert = entity.alert
                entity_data["alert"] = {
                    "cause": alert.cause,
                    "effect": alert.effect,
                    "description_text": alert.description_text.translation[0].text if alert.description_text.translation else None
                }
            
            entities.append(entity_data)
        
        return json.dumps({"header": {
            "gtfs_realtime_version": feed.header.gtfs_realtime_version,
            "timestamp": feed.header.timestamp
        }, "entities": entities}, indent=4)  # Convert to formatted JSON
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=4)
        
if __name__ == '__main__':
    file_path = "gtfs-realtime"  # Replace with the actual file path
    json_output = parse_gtfs_realtime(file_path)
    print(json_output)

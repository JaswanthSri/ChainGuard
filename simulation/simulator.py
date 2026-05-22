import time
import json
import random
import threading
from datetime import datetime
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# --- CONFIGURATION ---
ENDPOINT = "a33oq8caya7891-ats.iot.ap-south-1.amazonaws.com"
TOPIC = "trucks/telemetry"

PATH_TO_CERT = "certs/device.pem.crt"
PATH_TO_KEY = "certs/private.pem.key"
PATH_TO_ROOT_CA = "certs/AmazonRootCA1.pem"

# 5 Unique geographical routes for your fleet expansion
ROUTES = {
    "truck-01": [
        {"lat": 40.7128, "lng": -74.0060},  # NY Start
        {"lat": 40.7306, "lng": -73.9352},
        {"lat": 40.7589, "lng": -73.9851},
        {"lat": 41.0339, "lng": -73.7629}   # White Plains
    ],
    "truck-02": [
        {"lat": 34.0522, "lng": -118.2437}, # LA Start
        {"lat": 34.0407, "lng": -118.2695},
        {"lat": 34.0928, "lng": -118.3287},
        {"lat": 34.1425, "lng": -118.2551}  # Glendale
    ],
    "truck-03": [
        {"lat": 41.8781, "lng": -87.6298},  # Chicago Start
        {"lat": 41.8981, "lng": -87.6298},
        {"lat": 41.9742, "lng": -87.9073}   # O'Hare
    ],
    "truck-04": [
        {"lat": 25.7617, "lng": -80.1918},  # Miami Start
        {"lat": 25.7906, "lng": -80.1300},
        {"lat": 25.8576, "lng": -80.1242}   # Miami Beach
    ],
    "truck-05": [
        {"lat": 47.6062, "lng": -122.3321}, # Seattle Start
        {"lat": 47.6101, "lng": -122.3421},
        {"lat": 47.6205, "lng": -122.3493}   # Space Needle
    ]
}

def run_truck_simulation(truck_id, route_waypoints):
    """Worker loop executing inside individual independent threads for each truck asset."""
    print(f"[{truck_id}] Establishing secure connection to IoT Core...")
    
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        port=8883,
        cert_filepath=PATH_TO_CERT,
        pri_key_filepath=PATH_TO_KEY,
        ca_filepath=PATH_TO_ROOT_CA,
        client_id=truck_id, # Must be unique per client connection
        clean_session=False,
        keep_alive_secs=30
    )
    
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print(f"[{truck_id}] Secure TLS channel established successfully!")

    step = 0
    current_temp = 4.0  # Safe storage baseline target (4°C)
    
    try:
        while True:
            # Cycle or hold through route waypoints
            waypoint_index = min(step, len(route_waypoints) - 1)
            base_location = route_waypoints[waypoint_index]
            
            # Subtle positional tracking drift
            lat = base_location["lat"] + random.uniform(-0.0008, 0.0008)
            lng = base_location["lng"] + random.uniform(-0.0008, 0.0008)
            
            # --- ERRATIC TEMPERATURE ENGINE ---
            if truck_id == "truck-01":
                if step > 4:
                    # Simulates a faulty compressor engine cycling wildly around critical trip limits
                    # Yields jumps like: 8.2 -> 8.1 -> 7.0 -> 8.9 -> 6.4
                    current_temp = random.choice([8.2, 8.1, 7.0, 6.0, 7.1, 8.9, 9.2, 6.8, 8.5])
                else:
                    current_temp += random.uniform(-0.2, 0.2)
            elif truck_id == "truck-04" and step > 8:
                # Simulates a slower alternative drift anomaly pattern for diversity
                current_temp = random.choice([7.4, 7.9, 8.3, 8.1, 7.6, 8.6])
            else:
                # Standard healthy cooling bounds fluctuation (truck-02, truck-03, truck-05)
                current_temp = max(2.0, min(5.5, current_temp + random.uniform(-0.3, 0.3)))
                
            # Randomize baseline environmental humidity factor
            humidity = max(10.0, min(95.0, 52.0 + random.uniform(-4.0, 4.0)))
            
            # Simulated driver security tracking check opens
            door_status = "open" if (step == 3 and truck_id == "truck-03") else "closed"
            
            payload = {
                "truckId": truck_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "temperature": round(current_temp, 2),
                "humidity": round(humidity, 2),
                "doorStatus": door_status
            }
            
            json_payload = json.dumps(payload)
            mqtt_connection.publish(
                topic=TOPIC,
                payload=json_payload,
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            print(f"[{truck_id}] Broadcast -> Temp: {payload['temperature']}°C | Lat: {payload['latitude']}")
            
            step += 1
            time.sleep(5)  # Fleet interval check heartbeat [cite: 12, 44]
            
    except Exception as e:
        print(f"[{truck_id}] Encountered runtime event error: {str(e)}")

def main():
    print("Initializing ChainGuard Multi-Vehicle Fleet Simulator (5 Active Assets)...")
    threads = []
    
    for truck_id, route in ROUTES.items():
        t = threading.Thread(target=run_truck_simulation, args=(truck_id, route), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(1.2)  # Stagger outbound connection handshakes to prevent network lockup
        
    print("\n[FLEET ONLINE] All 5 vehicle threads reporting telemetry logs. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nHalting cluster simulation. Disconnecting threads cleanly...")

if __name__ == "__main__":
    main()
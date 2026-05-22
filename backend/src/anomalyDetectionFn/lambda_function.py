import json
import boto3
import math
from datetime import datetime

# Initialize DynamoDB clients
dynamodb = boto3.resource('dynamodb')
routes_table = dynamodb.Table('Routes')
alerts_table = dynamodb.Table('Alerts')
trucks_table = dynamodb.Table('Trucks')

# --- CONFIGURABLE THRESHOLDS ---
MAX_SAFE_TEMP = 8.0  # Max degrees Celsius allowed for the cold-chain cargo
GEOCORRIDOR_THRESHOLD_KM = 5.0  # Maximum allowed deviation from any waypoint

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in kilometers.
    """
    R = 6371.0 # Earth's radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def check_geospatial_route(truck_id, current_lat, current_lng):
    """
    Checks if the vehicle's position is within the acceptable 
    corridor of its planned checkpoints.
    """
    try:
        response = routes_table.get_item(Key={'truckId': truck_id})
        if 'Item' not in response:
            print(f"No planned route map found for {truck_id}. Skipping route check.")
            return False, 0.0
        
        corridor = response['Item'].get('allowedCorridor', [])
        min_distance = float('inf')
        
        # Find the distance to the closest route waypoint
        for waypoint in corridor:
            wp_lat = float(waypoint['lat'])
            wp_lng = float(waypoint['lng'])
            dist = haversine_distance(current_lat, current_lng, wp_lat, wp_lng)
            if dist < min_distance:
                min_distance = dist
                
        if min_distance > GEOCORRIDOR_THRESHOLD_KM:
            return True, round(min_distance, 2)
            
        return False, round(min_distance, 2)
    except Exception as e:
        print(f"Error evaluating geo-route: {str(e)}")
        return False, 0.0

def lambda_handler(event, context):
    """
    Evaluates incoming telemetry for temperature spikes and geospatial route deviations.
    Updates the overall health state and logs distinct incidents to the Alerts table.
    """
    print("Evaluating telemetry packet:", json.dumps(event))
    
    truck_id = event.get('truckId')
    timestamp = event.get('timestamp')
    current_temp = float(event.get('temperature', 0))
    lat = float(event.get('latitude', 0))
    lng = float(event.get('longitude', 0))
    
    anomalies_detected = []
    status_state = "NORMAL"

    # 1. Evaluate Temperature Excursions
    if current_temp > MAX_SAFE_TEMP:
        anomalies_detected.append({
            'type': 'TEMPERATURE_EXCURSION',
            'severity': 'CRITICAL',
            'message': f"Temperature spike detected: {current_temp}°C exceeds safety cap of {MAX_SAFE_TEMP}°C."
        })
        status_state = "CRITICAL"

    # 2. Evaluate Route Violations
    is_off_route, deviation_km = check_geospatial_route(truck_id, lat, lng)
    if is_off_route:
        anomalies_detected.append({
            'type': 'ROUTE_DEVIATION',
            'severity': 'WARNING',
            'message': f"Truck drifted {deviation_km} km outside its assigned transit corridor."
        })
        if status_state != "CRITICAL":
            status_state = "WARNING"

    # 3. Actions taken based on findings
    if anomalies_detected:
        for anomaly in anomalies_detected:
            alert_item = {
                'truckId': truck_id,
                'timestamp': timestamp,
                'anomalyType': anomaly['type'],
                'severity': anomaly['severity'],
                'message': anomaly['message'],
                'metrics': {
                    'temperature': str(current_temp),
                    'latitude': str(lat),
                    'longitude': str(lng)
                }
            }
            print(f"Logging incident alert: {anomaly['type']}")
            alerts_table.put_item(Item=alert_item)
            
    # 4. Update core state table cache with actual status label
    try:
        trucks_table.update_item(
            Key={'truckId': truck_id},
            UpdateExpression="SET #s = :status_val",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':status_val': status_state}
        )
    except Exception as e:
        print(f"Could not sync status health attribute: {str(e)}")

    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed anomalies. Status resolved to: {status_state}")
    }
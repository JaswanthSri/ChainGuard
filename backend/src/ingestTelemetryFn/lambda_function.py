import os
import json
import boto3
from datetime import datetime

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
telemetry_table = dynamodb.Table('Telemetry')
trucks_table = dynamodb.Table('Trucks')

def lambda_handler(event, context):
    """
    Triggered by AWS IoT Core rule action.
    Parses, validates, and stores incoming truck telemetry data.
    """
    print("Received event:", json.dumps(event))
    
    # 1. Extract and validate required payload parameters
    truck_id = event.get('truckId')
    timestamp = event.get('timestamp')
    lat = event.get('latitude')
    lng = event.get('longitude')
    temp = event.get('temperature')
    humidity = event.get('humidity')
    door_status = event.get('doorStatus')
    
    if not truck_id or not timestamp:
        print("Error: Missing primary keys (truckId or timestamp). Dropping payload.")
        return {"statusCode": 400, "body": "Missing vital keys"}
        
    try:
        # 2. Build our normalized storage models
        # DynamoDB handles decimal numbers best when kept as floats/ints, but boto3 converts floats
        # to Decimal type automatically if they are clean, or we parse them clearly.
        telemetry_item = {
            'truckId': str(truck_id),
            'timestamp': str(timestamp),
            'latitude': str(lat),
            'longitude': str(lng),
            'temperature': str(temp),
            'humidity': str(humidity),
            'doorStatus': str(door_status),
            'processedAt': datetime.utcnow().isoformat() + "Z"
        }
        
        truck_state_item = {
            'truckId': str(truck_id),
            'lastTimestamp': str(timestamp),
            'latitude': str(lat),
            'longitude': str(lng),
            'currentTemperature': str(temp),
            'currentHumidity': str(humidity),
            'doorStatus': str(door_status),
            'status': "NORMAL"  # Default status; anomaly detection logic will update this later
        }
        
        # 3. Concurrent/Sequential writes to DynamoDB
        print(f"Persisting historical ledger item for {truck_id}")
        telemetry_table.put_item(Item=telemetry_item)
        
        print(f"Updating latest state cache for {truck_id}")
        trucks_table.put_item(Item=truck_state_item)
        
        print(f"Invoking anomaly detection worker asynchronously for {truck_id}")
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName='anomalyDetectionFn',
            InvocationType='Event',  # 'Event' makes it an asynchronous, fire-and-forget call
            Payload=json.dumps(event)
        )

        
        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully processed telemetry for truck {truck_id}")
        }
        
    except Exception as e:
        print(f"Error persisting telemetry data: {str(e)}")
        raise e
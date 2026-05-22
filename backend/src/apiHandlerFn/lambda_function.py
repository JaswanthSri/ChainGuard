import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
trucks_table = dynamodb.Table('Trucks')
alerts_table = dynamodb.Table('Alerts')

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB numeric types to standard JSON floats/ints."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    path = event.get('resource', '')
    http_method = event.get('httpMethod', '')
    
    # Define standard CORS headers so your browser doesn't block local file requests
    cors_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }
    
    print(f"Handling {http_method} request for route: {path}")

    try:
        if "/trucks" in path:
            response = trucks_table.scan()
            items = response.get('Items', [])
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(items, cls=DecimalEncoder)
            }
            
        elif "/alerts" in path:
            response = alerts_table.scan()
            items = response.get('Items', [])
            # Sort newest alerts to the top
            sorted_items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(sorted_items, cls=DecimalEncoder)
            }
            
        return {
            "statusCode": 404,
            "headers": cors_headers,
            "body": json.dumps({"error": "Route not found"})
        }
    except Exception as e:
        print(f"API Execution Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)})
        }
import boto3
from django.conf import settings
import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Initialize environment variables
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# Initialize DynamoDB client
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=env("AWS_ACCESS_KEY_ID", default=""),
    aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY", default=""),
    region_name=env("AWS_REGION", default="eu-north-1"),
)

# Reference the inventory table
table = dynamodb.Table(env("DYNAMODB_TABLE_NAME", default="Inventory"))
realtime_table = dynamodb.Table(env("INVENTORY_REALTIME_DYNAMODB_TABLE_NAME", default="Inventory_realtime_data"))
purchase_table = dynamodb.Table(env("INVENTORY_PURCHASE_DETAILS_DYNAMODB_TABLE_NAME", default="Inventory_purchase_details"))
threshold_table = dynamodb.Table(env("INVENTORY_THRESHOLD_AUTOORDER_DYNAMODB_TABLE_NAME", default="Inventory_threshold_autoorder"))


def upload_to_dynamodb(json_file_path):
    import json

    try:
        # Load JSON File
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Iterate through each item
        for item in data:
            table.put_item(
                Item={
                    "ItemID": int(item["ItemID"]),
                    "Name": item["Name"],
                    "Category": item["Category"],
                    "Quantity": int(item["Quantity"]),
                    "InShelf": item["InShelf"],
                    "AutoOrder": item["AutoOrder"],
                    "PurchaseDate": item["PurchaseDate"],
                    "Supplier": item["Supplier"],
                    "Units": item["Units"]
                }
            )
            print(f"Uploaded: {item['Name']}")

    except Exception as e:
        print(f"Error uploading data: {e}")


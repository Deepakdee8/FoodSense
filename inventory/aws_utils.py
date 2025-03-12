import boto3
from django.conf import settings
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Initialize environment variables
# env = environ.Env()
# environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

load_dotenv()
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key

aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key

aws_region = os.getenv("AWS_REGION")
os.environ["AWS_REGION"] = aws_region

dummy_table = os.getenv("DYNAMODB_TABLE_NAME")
os.environ["DYNAMODB_TABLE_NAME"] = dummy_table

realtime_table_name = os.getenv("INVENTORY_REALTIME_DYNAMODB_TABLE_NAME")
os.environ["INVENTORY_REALTIME_DYNAMODB_TABLE_NAME"] = realtime_table_name

purchase_table_name = os.getenv("INVENTORY_PURCHASE_DETAILS_DYNAMODB_TABLE_NAME")
os.environ["INVENTORY_PURCHASE_DETAILS_DYNAMODB_TABLE_NAME"] = purchase_table_name

threshold_table_name = os.getenv("INVENTORY_THRESHOLD_AUTOORDER_DYNAMODB_TABLE_NAME")
os.environ["INVENTORY_THRESHOLD_AUTOORDER_DYNAMODB_TABLE_NAME"] = threshold_table_name

autoorder_table_name = os.getenv("INVENTORY_AUTOORDER_LIST_TABLE_NAME")
os.environ["INVENTORY_AUTOORDER_LIST_TABLE_NAME"] = autoorder_table_name

# Initialize DynamoDB client
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id = aws_access_key,
    aws_secret_access_key = aws_secret_key,
    region_name = aws_region,
)

# Reference the inventory table
table = dynamodb.Table(dummy_table)
realtime_table = dynamodb.Table(realtime_table_name)
purchase_table = dynamodb.Table(purchase_table_name)
threshold_table = dynamodb.Table(threshold_table_name)
autoorder_table = dynamodb.Table(autoorder_table_name)


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


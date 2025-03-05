from django.db import models
from django.contrib.auth.models import User
import boto3
from django.conf import settings
# Initialize DynamoDB client
from .aws_utils import table

# Create your models here.

# Function to add an item to DynamoDB
def add_item(item):
    table.put_item(Item=item)

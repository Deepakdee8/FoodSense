import json
import os
from decimal import Decimal
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Initialize DynamoDB client
from .aws_utils import table,realtime_table,purchase_table,threshold_table,autoorder_table
from .aws_utils import upload_to_dynamodb

# Store auto-order items in a global list (or use a database)
AUTO_ORDER_LIST = []

# Login view
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect("index")  # Redirect to inventory page
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "login.html")

# Logout view
def user_logout(request):
    logout(request)
    return redirect("login")  

# @login_required(login_url="login")
def index(request):

    # Scan DynamoDB table
    response = table.scan()
    items = response.get('Items', [])
    return render(request, 'index.html', {'items': items})

def scan_dynamodb_table(table):
    items = []
    response = table.scan()
    items.extend(response.get('Items', []))

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    return items

# @login_required(login_url="login")
def inventory(request):
    # items_realtime = scan_dynamodb_table(realtime_table)
    # items_purchase = scan_dynamodb_table(purchase_table)
    # items_threshold = scan_dynamodb_table(threshold_table)

    # threshold_response = threshold_table.scan()
    # items_threshold = threshold_response.get('Items', [])
    # items_threshold.sort(key=lambda x: int(x["ItemID"]))

    # return JsonResponse({
    # 'items_realtime': items_realtime,
    # 'items_purchase': items_purchase,
    # 'items_threshold': items_threshold
    # })

    return render(request, 'upload_data.html', {
        # 'items_realtime': items_realtime,
        # 'items_purchase': items_purchase,
        # 'items_threshold': items_threshold
    })

def threshold_levels(request):
    threshold_response = threshold_table.scan()
    items_threshold = threshold_response.get('Items', [])
    items_threshold.sort(key=lambda x: int(x["ItemID"]))

     # Count "Yes" and "No" values in AutoOrderSet
    # auto_order_yes = sum(1 for item in items_threshold if item.get("AutoOrderSet", "").lower() == "yes")
    # auto_order_no = sum(1 for item in items_threshold if item.get("AutoOrderSet", "").lower() == "no")


    # return JsonResponse({
    # 'items_threshold': items_threshold
    # })

    return render(request, 'threshold.html', {
         'items_threshold': items_threshold
        #  'auto_order_yes': auto_order_yes,
        #  'auto_order_no': auto_order_no
    })

def purchase_details(request):
    purchase_response = purchase_table.scan()
    items_purchase = purchase_response.get('Items', [])
    items_purchase.sort(key=lambda x: int(x["ItemID"]))

    # return JsonResponse({
    # 'items_threshold': items_threshold
    # })

    return render(request, 'purchase.html', {
        'items_purchase': items_purchase
    })

def order_details(request):
    order_response = autoorder_table.scan()
    items_order = order_response.get('Items', [])
    items_order.sort(key=lambda x: int(x["ItemID"]))

    # return JsonResponse({
    # 'items_threshold': items_threshold
    # })

    return render(request, 'order.html', {
        'items_order': items_order
    })

def realtime_inventory(request):
    inventory_response = realtime_table.scan()
    items_realtime = inventory_response.get('Items', [])
    items_realtime.sort(key=lambda x: int(x["ItemID"]))

    # return JsonResponse({
    # 'items_threshold': items_threshold
    # })

    return render(request, 'realtime.html', {
        'items_realtime': items_realtime
    })

def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        # Save the uploaded file to the 'media' directory
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        try:
            # Read the Excel file and convert it to JSON
            df = pd.read_excel(file_path)
            json_data = df.to_json(orient='records')

            # Save JSON to a file in 'media' directory
            json_filename = filename.rsplit('.', 1)[0] + '.json'
            json_path = os.path.join(settings.MEDIA_ROOT, json_filename)

            with open(json_path, 'w') as json_file:
                json.dump(json.loads(json_data), json_file, indent=4)

            messages.success(request, f"File Converted to JSON successfully! Stored as {json_filename}")

        except Exception as e:
            messages.error(request, f"Error processing file: {e}")

        return redirect('upload_excel')

    return render(request, 'upload_data.html')

def upload_to_cloud(request):
    if request.method == 'POST':
        # Get the latest JSON file in media/
        media_folder = settings.MEDIA_ROOT
        json_files = [f for f in os.listdir(media_folder) if f.endswith('.json')]
        
        if not json_files:
            messages.error(request, "No JSON file found. Upload an Excel file first.")
            return render(request, 'upload_data.html')

        latest_json_file = max(json_files, key=lambda f: os.path.getctime(os.path.join(media_folder, f)))
        json_path = os.path.join(media_folder, latest_json_file)

        # Load JSON data
        with open(json_path, 'r') as file:
            data = json.load(file)


        # Upload data to DynamoDB
        for item in data:
            try:
                purchase_table.put_item(
                    Item={
                        "ItemID": int(item["ItemID"]),
                        "ItemName": item["ItemName"],
                        "Category": item["Category"],
                        "Supplier": int(item["Supplier"]),
                        "PurchaseDate": item["PurchaseDate"],
                        "InvoiceNumber": item["InvoiceNumber"],
                    }
                )
            except Exception as e:
                messages.error(request, f"Error uploading {item['Name']}: {e}")

        messages.success(request, f"All Items Uploaded")
        return render(request, 'upload_data.html')

    messages.error(request, "Error uploading data")
    return render(request, 'upload_data.html')

def get_least_quantity_items(request):
    try:
        # Scan entire table (or use a query if possible)
        response = threshold_table.scan()
        items = response.get('Items', [])

        # Sort by Quantity and take the top 10 least items
        sorted_items = sorted(items, key=lambda x: int(x['Threshold']))

        return JsonResponse({'items': sorted_items}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def add_item(request):
    if request.method == "POST":
        try:
            item_id = request.POST.get("ItemID")
            item_name = request.POST.get("itemname")
            threshold_value = request.POST.get("thresholdvalue")
            units = request.POST.get("unit")
            auto_order = request.POST.get("autoReorder")
            required_quantity = request.POST.get("requiredquantity")

            # Convert threshold_value to Decimal (DynamoDB does not accept float)
            threshold_value = Decimal(threshold_value)
            required_quantity = Decimal(required_quantity)

            # Store data in DynamoDB
            threshold_table.put_item(
                Item={
                    "ItemID": item_id,  # Convert to string as DynamoDB expects keys as strings
                    "ItemName": item_name,
                    "Threshold": threshold_value,
                    "Units": units,
                    "Autoorder": "Yes" if auto_order == "yes" else "No",
                    "RequiredQuantity" : required_quantity
                }
            )

            messages.success(request, "Item added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding item: {e}")

    return redirect("threshold_levels")

def edit_item(request, item_id):
    if request.method == "POST":
        try:
            item_name = request.POST.get("itemname")
            threshold_value = request.POST.get("thresholdvalue")
            unit = request.POST.get("unit")
            auto_order = request.POST.get("autoReorder")
            required_quantity = request.POST.get("requiredquantity")

            # Convert threshold_value and required_quantity to Decimal
            threshold_value = Decimal(threshold_value)
            required_quantity = Decimal(required_quantity)
            item_id = str(item_id)  
            # Update the item in DynamoDB
            threshold_table.update_item(
                Key={"ItemID": item_id},
                UpdateExpression="SET ItemName = :name, Threshold = :threshold, Units = :unit, Autoorder = :auto, RequiredQuantity = :required",
                ExpressionAttributeValues={
                    ":name": item_name,
                    ":threshold": threshold_value,
                    ":unit": unit,
                    ":auto": "Yes" if auto_order == "yes" else "No",
                    ":required": required_quantity,
                },
            )

            messages.success(request, "Item updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating item: {e}")

    return redirect("threshold_levels")

def delete_item(request, item_id):
    try:
        # Delete item from DynamoDB
        threshold_table.delete_item(Key={"ItemID": str(item_id)})
        messages.success(request, "Item deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting item: {e}")

    return redirect("threshold_levels")


@csrf_exempt
def receive_autoorder(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"Raw data: ",data)
            autoorder_list = data.get("autoorder_list", [])
            print(f"auto order list received:",autoorder_list)
            # AUTO_ORDER_LIST.clear()
            AUTO_ORDER_LIST.extend(autoorder_list)
            return JsonResponse({"message": "Auto-order data received", "data": AUTO_ORDER_LIST}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "GET":
            data = json.loads(request.body)
            print(f"Raw data: ",data)
            autoorder_list = data.get("autoorder_list", [])
            print(f"auto order list received:",autoorder_list)
            # AUTO_ORDER_LIST.clear()
            AUTO_ORDER_LIST.extend(autoorder_list)
            return JsonResponse({"message": "Auto-order data received", "data": AUTO_ORDER_LIST}, status=200)

    return JsonResponse({"error": "Invalid request"}, status=400)
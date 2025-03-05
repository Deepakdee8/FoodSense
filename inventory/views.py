import json
import os
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
# Initialize DynamoDB client
from .aws_utils import table,realtime_table,purchase_table,threshold_table
from .aws_utils import upload_to_dynamodb



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

def inventory(request):
    items_realtime = scan_dynamodb_table(realtime_table)
    items_purchase = scan_dynamodb_table(purchase_table)
    items_threshold = scan_dynamodb_table(threshold_table)

    # return JsonResponse({
    # 'items_realtime': items_realtime,
    # 'items_purchase': items_purchase,
    # 'items_threshold': items_threshold
    # })

    return render(request, 'inventory.html', {
        'items_realtime': items_realtime,
        'items_purchase': items_purchase,
        'items_threshold': items_threshold
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

    return render(request, 'index.html')


def upload_to_cloud(request):
    if request.method == 'POST':
        # Get the latest JSON file in media/
        media_folder = settings.MEDIA_ROOT
        json_files = [f for f in os.listdir(media_folder) if f.endswith('.json')]
        
        if not json_files:
            messages.error(request, "No JSON file found. Upload an Excel file first.")
            return render(request, 'index.html')

        latest_json_file = max(json_files, key=lambda f: os.path.getctime(os.path.join(media_folder, f)))
        json_path = os.path.join(media_folder, latest_json_file)

        # Load JSON data
        with open(json_path, 'r') as file:
            data = json.load(file)

        # Upload data to DynamoDB
        for item in data:
            try:
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
            except Exception as e:
                messages.error(request, f"Error uploading {item['Name']}: {e}")

        messages.success(request, f"All Items Uploaded")
        return render(request, 'index.html')

    messages.error(request, "Error uploading data")
    return render(request, 'index.html')

def get_least_quantity_items(request):
    try:
        # Scan entire table (or use a query if possible)
        response = table.scan()
        items = response.get('Items', [])

        # Sort by Quantity and take the top 10 least items
        sorted_items = sorted(items, key=lambda x: int(x['Quantity']))[:10]

        return JsonResponse({'items': sorted_items}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


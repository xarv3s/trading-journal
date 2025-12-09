import requests
import json

url = "http://localhost:8000/api/v1/orders/place"
payload = {
    "tradingsymbol": "INFY",
    "exchange": "NSE",
    "transaction_type": "BUY",
    "quantity": 1,
    "price": 1500.0,
    "product": "MIS",
    "order_type": "LIMIT",
    "variety": "regular"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

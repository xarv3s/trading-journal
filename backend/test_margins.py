import requests
import json

BASE_URL = "http://localhost:8000/api/v1/market-data/margins"

def test_margins():
    print("Testing Margins API...")
    
    payload = [
        {
            "type": "TRADE",
            "id": "test_trade_1",
            "constituents": [{
                "exchange": "NSE",
                "tradingsymbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": 1,
                "product": "CNC"
            }]
        },
        {
            "type": "BASKET",
            "id": "test_basket_1",
            "constituents": [
                {
                    "exchange": "NFO",
                    "tradingsymbol": "NIFTY24DEC24000CE",
                    "transaction_type": "SELL",
                    "quantity": 50,
                    "product": "NRML"
                },
                {
                    "exchange": "NFO",
                    "tradingsymbol": "NIFTY24DEC24500CE",
                    "transaction_type": "BUY",
                    "quantity": 50,
                    "product": "NRML"
                }
            ]
        }
    ]
    
    try:
        response = requests.post(BASE_URL, json=payload)
        if response.status_code == 200:
            print("Success!")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 401:
            print("Success (401 Expected if not logged in):")
            print(response.json())
        else:
            print(f"Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_margins()

import requests
import json

def test_api_add_to_basket():
    url = "http://localhost:8000/api/v1/trades/basket/57/add" # Assuming basket ID 57 from previous context or just a placeholder
    # Wait, I need a valid basket ID and trade ID.
    # I'll fetch open trades first to find a basket and a trade.
    
    base_url = "http://localhost:8000/api/v1/trades"
    
    try:
        # 1. Fetch Open Trades
        response = requests.get(f"{base_url}/open")
        print(f"Fetch Open Trades Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching trades: {response.text}")
            return
            
        trades = response.json()
        
        basket = next((t for t in trades if t.get('is_basket') == 1), None)
        trade = next((t for t in trades if t.get('is_basket') == 0), None)
        
        if not basket or not trade:
            print("Could not find a basket or a trade to test with.")
            return

        print(f"Testing with Basket ID: {basket['id']} and Trade ID: {trade['id']}")
        
        # 2. Add to Basket
        payload = {
            "trade_ids": [trade['id']]
        }
        
        add_url = f"{base_url}/basket/{basket['id']}/add"
        print(f"Sending POST to {add_url} with payload: {payload}")
        
        response = requests.post(add_url, json=payload)
        
        if response.status_code == 200:
            print("Success! API returned 200 OK")
            print(response.json())
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_add_to_basket()

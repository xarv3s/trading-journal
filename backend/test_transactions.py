import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000/api/v1/transactions/"

def test_transactions():
    print("Testing Transactions API...")
    
    # 1. Create Deposit
    payload = {
        "date": str(date.today()),
        "amount": 10000.0,
        "type": "DEPOSIT",
        "notes": "Initial Deposit"
    }
    print(f"Creating transaction: {payload}")
    response = requests.post(BASE_URL, json=payload)
    if response.status_code == 200:
        print(" - Success")
        txn = response.json()
        txn_id = txn['id']
    else:
        print(f" - Failed: {response.text}")
        return

    # 2. List Transactions
    print("Listing transactions...")
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        txns = response.json()
        print(f" - Found {len(txns)} transactions")
        found = False
        for t in txns:
            if t['id'] == txn_id:
                found = True
                print(f" - Verified created transaction: {t}")
                break
        if not found:
            print(" - ERROR: Created transaction not found in list")
    else:
        print(f" - Failed: {response.text}")

    # 3. Delete Transaction
    print(f"Deleting transaction {txn_id}...")
    response = requests.delete(f"{BASE_URL}{txn_id}")
    if response.status_code == 200:
        print(" - Success")
    else:
        print(f" - Failed: {response.text}")

    # 4. Verify Deletion
    response = requests.get(BASE_URL)
    txns = response.json()
    found = False
    for t in txns:
        if t['id'] == txn_id:
            found = True
            break
    if not found:
        print(" - Verified deletion (Transaction gone)")
    else:
        print(" - ERROR: Transaction still exists")

if __name__ == "__main__":
    test_transactions()

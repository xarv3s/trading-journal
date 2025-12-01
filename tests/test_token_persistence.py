import os
from services.kite_service import KiteClient
import json

def test_token_persistence():
    print("\n--- Testing Token Persistence ---")
    
    token = "test_access_token_123"
    filepath = "test_token.json"
    
    # 1. Save Token
    client = KiteClient(api_key="dummy")
    client.save_access_token(token, filepath=filepath)
    
    assert os.path.exists(filepath)
    print("Token file created.")
    
    # 2. Load Token
    loaded_token = KiteClient.load_access_token(filepath=filepath)
    assert loaded_token == token
    print(f"Token loaded successfully: {loaded_token}")
    
    # 3. Cleanup
    os.remove(filepath)
    print("Cleanup done.")
    
    print("Token Persistence Test Passed!")

if __name__ == "__main__":
    test_token_persistence()

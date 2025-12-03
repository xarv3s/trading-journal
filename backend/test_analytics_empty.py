import sys
import os
import pandas as pd

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.services.analytics_service import AnalyticsService

def test_empty_analytics():
    print("Testing AnalyticsService with empty data...")
    service = AnalyticsService([])
    
    try:
        dist = service.get_pnl_distribution()
        print(f"get_pnl_distribution returned type: {type(dist)}")
        
        as_list = dist.tolist()
        print(f"tolist() result: {as_list}")
        
        if isinstance(as_list, list) and len(as_list) == 0:
            print("TEST PASSED")
        else:
            print("TEST FAILED: Result is not an empty list")
            
    except Exception as e:
        print(f"TEST FAILED with exception: {e}")

if __name__ == "__main__":
    test_empty_analytics()

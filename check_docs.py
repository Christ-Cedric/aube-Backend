import requests
import json
import sys

try:
    response = requests.get("http://localhost:8001/openapi.json")
    if response.status_code != 200:
        print(f"Error fetching OpenAPI: Status {response.status_code}")
        sys.exit(1)
        
    data = response.json()
    paths = data.get("paths", {})
    
    print(f"Total Paths in OpenAPI: {len(paths)}")
    
    auth_endpoints = [p for p in paths if "/auth/signup" in p or "/auth/login" in p]
    
    if auth_endpoints:
        print("Auth Endpoints FOUND in OpenAPI:")
        for p in auth_endpoints:
            print(f" - {p}")
    else:
        print("Auth Endpoints NOT FOUND in OpenAPI.")
        print("Available paths sample:", list(paths.keys())[:5])
        
except Exception as e:
    print(f"Connection failed: {e}")

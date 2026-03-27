import sys
import os
# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.main import app
from fastapi.routing import APIRoute

print("Checking registered routes...")
auth_found = False
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ", ".join(route.methods)
        print(f"Path: {route.path} | Methods: {methods} | Name: {route.name}")
        if "/v1/auth/signup" in route.path:
            auth_found = True

if auth_found:
    print("\nSUCCESS: Auth endpoints are present.")
else:
    print("\nFAILURE: Auth endpoints are MISSING.")

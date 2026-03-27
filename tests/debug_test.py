import asyncio
import sys
import os
sys.path.append(os.getcwd())

print("Starting debug...")
try:
    from app.main import app
    print("Imported app.main")
    from app.models.user import User
    print("Imported User model")
    from app.core.config import settings
    print("Imported settings")
    print(settings.model_dump())
except Exception as e:
    import traceback
    traceback.print_exc()

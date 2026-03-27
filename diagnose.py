"""
Script de diagnostic pour backend_for_app
Teste tous les composants critiques
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mongodb():
    """Test MongoDB connection"""
    try:
        from app.core.database import db
        await db.connect_to_database()
        # Test a simple operation
        await db.db.list_collection_names()
        print("✅ MongoDB: Connected successfully")
        await db.close_database_connection()
        return True
    except Exception as e:
        print(f"❌ MongoDB: {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await r.ping()
        print(f"✅ Redis: Connected successfully ({settings.REDIS_URL})")
        await r.close()
        return True
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

async def test_imports():
    """Test critical imports"""
    try:
        from app.main import app
        from app.api.v1 import auth, subscriptions, user, ads, websockets
        from app.services.user_service import UserService
        from app.services.subscription_service import SubscriptionService
        print("✅ Imports: All modules load successfully")
        return True
    except Exception as e:
        print(f"❌ Imports: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config():
    """Test configuration"""
    try:
        from app.core.config import settings
        print(f"✅ Config loaded:")
        print(f"   - MongoDB: {settings.MONGODB_URI}")
        print(f"   - Redis: {settings.REDIS_URL}")
        print(f"   - JWT Algorithm: {settings.JWT_ALGORITHM}")
        print(f"   - CORS: {settings.CORS_ORIGINS}")
        return True
    except Exception as e:
        print(f"❌ Config: {e}")
        return False

async def main():
    print("=" * 60)
    print("DIAGNOSTIC BACKEND_FOR_APP")
    print("=" * 60)
    print()
    
    results = {}
    
    print("1. Testing Configuration...")
    results['config'] = await test_config()
    print()
    
    print("2. Testing Imports...")
    results['imports'] = await test_imports()
    print()
    
    print("3. Testing MongoDB...")
    results['mongodb'] = await test_mongodb()
    print()
    
    print("4. Testing Redis...")
    results['redis'] = await test_redis()
    print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results.values())
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Backend is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

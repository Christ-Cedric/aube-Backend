"""
Script de test pour l'enregistrement d'appareil
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_device_registration():
    print("=" * 60)
    print("TEST: Enregistrement d'Appareil")
    print("=" * 60)
    print()
    
    # 1. Créer un utilisateur
    print("1. Création d'un utilisateur de test...")
    signup_data = {
        "email": "device_test@example.com",
        "password": "password123",
        "full_name": "Device Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/auth/signup", json=signup_data)
        if response.status_code == 201:
            print("   ✅ Utilisateur créé, connexion...")
            # Signup successful, now login
            login_data = {"email": signup_data["email"], "password": signup_data["password"]}
            response = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
            if response.status_code == 200:
                user_data = response.json()
                print("   ✅ Connecté")
            else:
                print(f"   ❌ Erreur login: {response.status_code} - {response.text}")
                return
        elif response.status_code == 409:
            print("   ℹ️  Utilisateur existe déjà, connexion...")
            # Login instead
            login_data = {"email": signup_data["email"], "password": signup_data["password"]}
            response = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
            if response.status_code == 200:
                user_data = response.json()
                print("   ✅ Connecté")
            else:
                print(f"   ❌ Erreur login: {response.status_code} - {response.text}")
                return
        else:
            print(f"   ❌ Erreur signup: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    token = user_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Enregistrer un appareil
    print("\n2. Enregistrement d'un appareil...")
    device_data = {
        "device_id": "test-device-001",
        "device_name": "Mon Téléphone de Test",
        "os_type": "Android"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/user/register-device",
            json=device_data,
            headers=headers
        )
        if response.status_code == 200:
            print("   ✅ Appareil enregistré")
            device = response.json()
            print(f"   Device ID: {device.get('device_id')}")
            print(f"   Device Name: {device.get('device_name')}")
            print(f"   Is Active: {device.get('is_active')}")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 3. Réenregistrer le même appareil (mise à jour)
    print("\n3. Réenregistrement du même appareil (mise à jour)...")
    device_data["device_name"] = "Mon Téléphone (Mis à jour)"
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/user/register-device",
            json=device_data,
            headers=headers
        )
        if response.status_code == 200:
            print("   ✅ Appareil mis à jour")
            device = response.json()
            print(f"   Device Name: {device.get('device_name')}")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 4. Lister les appareils
    print("\n4. Liste des appareils enregistrés...")
    try:
        response = requests.get(f"{BASE_URL}/v1/user/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            print(f"   ✅ {len(devices)} appareil(s) trouvé(s)")
            for dev in devices:
                print(f"      - {dev.get('device_name')} ({dev.get('device_id')})")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 5. Enregistrer un 2ème appareil
    print("\n5. Enregistrement d'un 2ème appareil...")
    device_data2 = {
        "device_id": "test-device-002",
        "device_name": "Ma Tablette",
        "os_type": "iOS"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/user/register-device",
            json=device_data2,
            headers=headers
        )
        if response.status_code == 200:
            print("   ✅ 2ème appareil enregistré")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 6. Vérifier le nombre total d'appareils
    print("\n6. Vérification du nombre total d'appareils...")
    try:
        response = requests.get(f"{BASE_URL}/v1/user/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            print(f"   ✅ Total: {len(devices)} appareil(s)")
            print("\n   Liste complète:")
            for dev in devices:
                print(f"      - {dev.get('device_name')} ({dev.get('device_id')}) - Active: {dev.get('is_active')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)

if __name__ == "__main__":
    test_device_registration()

import httpx
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def send_alert(file_path):
    print(f"Loading alert from: {file_path}")
    try:
        with open(file_path, 'r') as f:
            alert_payload = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON file: {e}")
        return

    auth_data = {'username': 'admin', 'password': 'password123'}
    
    try:
        with httpx.Client(timeout=30) as client:
            print("1. Authenticating with SOC backend...")
            r_auth = client.post(f"{API_BASE}/auth/login", data=auth_data)
            r_auth.raise_for_status()
            token = r_auth.json()['access_token']
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            print("2. Submitting alert payload...")
            r_alert = client.post(f"{API_BASE}/alert", json=alert_payload, headers=headers)
            r_alert.raise_for_status()
            
            print("\n✅ SUCCESS! Alert submitted.")
            print(f"Alert ID: {r_alert.json().get('id')}")
            
    except httpx.HTTPStatusError as e:
        print(f"\n❌ [FAIL] HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ [FAIL] Error connecting to SOC backend: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_custom_alert.py <path_to_json_file>")
        print("Example: python send_custom_alert.py demo_alert_high.json")
    else:
        send_alert(sys.argv[1])

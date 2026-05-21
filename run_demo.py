import sys
import httpx
import json
import time

# Force UTF-8 stdout to avoid encoding errors
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_BASE = "http://localhost:8000/api/v1"

def run_demo():
    print("=" * 60)
    print("SOC AUTOMATION BOT - LIVE DEMO TEST")
    print("=" * 60)

    auth_data = {'username': 'admin', 'password': 'password123'}

    try:
        with httpx.Client(timeout=30) as client:
            # --- Step 1: Authenticate ---
            print("\n[STEP 1] Authenticating with backend...")
            r_auth = client.post(f"{API_BASE}/auth/login", data=auth_data)
            r_auth.raise_for_status()
            token = r_auth.json()['access_token']
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            print("  -> Auth OK! Token received.")

            # --- Step 2: Send Alert ---
            alert_payload = {
                "source": "SentinelOne EDR",
                "severity": "High",
                "event_type": "Malware Outbreak Detection",
                "raw_data": {
                    "event_message": "Ransomware behavior detected. High entropy file modifications observed.",
                    "process_name": "unknown_encryptor.exe",
                    "file_path": "C:\\Users\\Finance\\Documents\\",
                    "source_ip": "185.220.101.14"
                }
            }

            print("\n[STEP 2] Alert payload:")
            print(json.dumps(alert_payload, indent=2))

            print("\n[STEP 3] Submitting alert to POST /api/v1/alert ...")
            start = time.time()
            r_alert = client.post(f"{API_BASE}/alert", json=alert_payload, headers=headers)
            r_alert.raise_for_status()
            elapsed = round(time.time() - start, 2)

            alert_id = r_alert.json().get('id', 'UNKNOWN')
            print(f"\n  -> SUCCESS! Pipeline accepted alert in {elapsed}s")
            print(f"  -> Alert ID: {alert_id}")
            print(f"  -> Full response: {json.dumps(r_alert.json(), indent=2)}")

            print("\n[DONE] Check your dashboard at http://localhost:5173")
            print("  1. New alert should appear via WebSocket instantly.")
            print("  2. Wait 3-5 sec for Celery to query VirusTotal / AbuseIPDB / OTX.")
            print("  3. Risk score will spike and trigger the Playbook.")
            print("  4. Check Jira & Slack for automated responses.")

    except httpx.HTTPStatusError as e:
        print(f"\n  [FAIL] HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        print("  Make sure FastAPI (port 8000) and Redis are running.")

if __name__ == "__main__":
    run_demo()

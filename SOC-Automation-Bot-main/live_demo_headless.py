import httpx
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def trigger_demo_alert():
    print("🚀 [DEMO 1] Sending a simulated Critical Alert to the SOC Bot...")
    
    # 1. Provide authentic credentials to bypass the security layer
    auth_data = {'username': 'admin', 'password': 'password123'}
    try:
        with httpx.Client() as client:
            print("  -> Authenticating with the backend...")
            r_auth = client.post(f"{API_BASE}/auth/login", data=auth_data)
            r_auth.raise_for_status()
            token = r_auth.json()['access_token']
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # 2. Construct the alert payload.
            # We are using 185.220.101.14 (a known malicious Tor exit node / Scanner IP)
            # This ensures VirusTotal returns a high risk score to trigger the Playbooks!
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
            
            print("\n  -> Injecting the following Alert Payload:")
            print(json.dumps(alert_payload, indent=2))
            
            print("\n⏳ Submitting to FastAPI Endpoint (POST /api/v1/alert)...")
            start_time = time.time()
            r_alert = client.post(f"{API_BASE}/alert", json=alert_payload, headers=headers)
            r_alert.raise_for_status()
            
            alert_id = r_alert.json().get('id', 'UNKNOWN')
            print(f"✅ Success! Pipeline accepted the alert in {round(time.time() - start_time, 2)} seconds.")
            print(f"  -> Generated Internal ID: {alert_id}")
            
            print("\n🧠 Look at your React Dashboard!")
            print("  1. The new alert should appear instantaneously via WebSockets.")
            print("  2. Wait 3-5 seconds for Celery to finish querying VirusTotal, AbuseIPDB, & OTX.")
            print("  3. The Risk Score will spike, triggering the 'High Severity Threat Response' Playbook.")
            print("  4. Check your Jira Board and Slack Channel for the automated responses!")
            
    except Exception as e:
        print(f"❌ Error communicating with the SOC bot: {e}")
        print("Please ensure the FastAPI backend (localhost:8000) and Redis are running.")

if __name__ == "__main__":
    print("-" * 60)
    print("🛡️ SOC AUTOMATION BOT - LIVE PRESENTATION DEMO 🛡️")
    print("-" * 60)
    print("Press ENTER to transmit the simulated ransomware alert...")
    
    trigger_demo_alert()


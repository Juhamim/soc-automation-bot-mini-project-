import httpx
try:
    auth_data = {'username': 'admin', 'password': 'password123'}
    with httpx.Client() as client:
        r = client.post('http://localhost:8000/api/v1/auth/login', data=auth_data)
        token = r.json()['access_token']
        resp = client.get('http://localhost:8000/api/v1/playbooks', headers={'Authorization': f'Bearer {token}'})
        print(f"STATUS {resp.status_code}")
        print(f"TEXT {resp.text}")
except Exception as e:
    print(e)

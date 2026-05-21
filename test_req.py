import httpx

login_data = {'username': 'admin', 'password': 'password123'}
r = httpx.post('http://localhost:8000/api/v1/auth/login', data=login_data)
token = r.json()['access_token']

r2 = httpx.get('http://localhost:8000/api/v1/threat-intel', headers={'Authorization': f'Bearer {token}'})
print(f'Status: {r2.status_code}')
print(f'Response: {r2.text}')

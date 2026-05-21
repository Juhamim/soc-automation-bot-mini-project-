import asyncio
import httpx
from app.core.config import settings

async def query_issuetype():
    project_key = settings.JIRA_PROJECT_KEY
    with open('jira_issuetypes.txt', 'w') as f:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{settings.JIRA_URL}/rest/api/3/project/{project_key}",
                auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN),
                headers={"Accept": "application/json"}
            )
            f.write(f"Status: {response.status_code}\n")
            if response.status_code == 200:
                data = response.json()
                types = data.get('issueTypes', [])
                for t in types:
                    f.write(f"IssueType: {t.get('name')} (ID: {t.get('id')})\n")
            else:
                f.write(f"Error: {response.text}\n")
asyncio.run(query_issuetype())

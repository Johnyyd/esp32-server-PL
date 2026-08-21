import asyncio
import httpx
from app.core.config import settings

async def main():
    if not settings.HA_URL or not settings.HA_TOKEN:
        print("Missing HA_URL or HA_TOKEN")
        return
        
    url = f"{settings.HA_URL.rstrip('/')}/api/states"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            states = response.json()
            for state in states:
                if state['entity_id'].startswith('switch.') and 'pc' in state['entity_id']:
                    print(f"Found switch: {state['entity_id']} - {state.get('attributes', {}).get('friendly_name')}")
        else:
            print("Failed to fetch from HA:", response.status_code)

if __name__ == "__main__":
    asyncio.run(main())

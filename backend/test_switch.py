import asyncio
from app.services.tools_service import control_switch
import sys

# Windows asyncio bug workaround
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    result = await control_switch("turn_on_pc", "turn_on")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())

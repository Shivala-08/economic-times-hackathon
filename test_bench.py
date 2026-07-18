from src.main import run_benchmark
import asyncio
import json

async def main():
    try:
        res = await run_benchmark(2)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print("ERROR:", e)

asyncio.run(main())

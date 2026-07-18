from src.main import run_benchmark
import asyncio
import json

async def main():
    try:
        res = await run_benchmark(2)
        print("Latency:", res["avg_latency_ms"])
        print("Accuracy:", res["accuracy_pct"])
    except Exception as e:
        print("ERROR:", e)

asyncio.run(main())

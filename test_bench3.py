from src.main import run_benchmark
import asyncio

async def main():
    res = await run_benchmark(3)
    print("Avg Latency:", res["avg_latency_ms"], "ms")
    print("Accuracy:", res["accuracy_pct"], "%")

asyncio.run(main())

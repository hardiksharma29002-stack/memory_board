#!/usr/bin/env python3
"""Benchmark latency of candidate clustering and group construction."""

import time
from api.app.database import engine
from api.app.engine.groups import build_candidate_groups


def run_benchmark():
    print("⏱️ Benchmarking Candidate Macro Album Generation Latency...")
    cues = ["setting_outdoors", "lighting_bright_daylight", "color_cool"]

    latencies = []
    for i in range(5):
        start = time.perf_counter()
        groups = build_candidate_groups(positive_cues=cues, target_engine=engine)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        print(f"Run {i+1}: {elapsed:.2f} ms ({len(groups)} albums generated)")

    avg_latency = sum(latencies) / len(latencies)
    print(f"\n📊 Average Latency: {avg_latency:.2f} ms")


if __name__ == "__main__":
    run_benchmark()

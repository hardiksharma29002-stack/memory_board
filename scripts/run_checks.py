#!/usr/bin/env python3
"""Run automated backend test suite and verification checks."""

import subprocess
import sys


def main():
    print("=" * 60)
    print("🚀 Running Memory Board Verification Suite")
    print("=" * 60)

    print("\n1. Running Pytest backend tests...")
    res = subprocess.run([sys.executable, "-m", "pytest", "api/tests", "-v"])
    if res.returncode != 0:
        print("❌ Backend tests failed!")
        sys.exit(res.returncode)

    print("\n✅ All checks passed successfully!")


if __name__ == "__main__":
    main()

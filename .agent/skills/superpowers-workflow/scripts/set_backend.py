#!/usr/bin/env python3
"""Script to switch the execution backend for Superpowers."""

import argparse
import sys
from pathlib import Path

# Add script directory to path to import config
script_dir = Path(__file__).parent.resolve()
sys.path.append(str(script_dir))

import config

def main():
    parser = argparse.ArgumentParser(description="Switch execution backend")
    parser.add_argument(
        "--backend",
        choices=["gemini", "claude"],
        required=True,
        help="Backend to use (gemini or claude)"
    )
    args = parser.parse_args()

    current_config = config.load_config()
    current_config["execution_backend"] = args.backend
    config.save_config(current_config)

    print(f"✅ Execution backend switched to: {args.backend}")
    print(f"Configuration saved to .agent/config.json")

if __name__ == "__main__":
    main()

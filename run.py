#!/usr/bin/env python3
"""BriefBot entry point: python run.py --config config.yaml --once"""
import sys

from briefbot.cli import main

if __name__ == "__main__":
    sys.exit(main())

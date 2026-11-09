"""Make the repo root importable so `briefbot` can be imported in tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

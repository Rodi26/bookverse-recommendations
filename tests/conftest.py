import sys, pathlib; p=str(pathlib.Path(__file__).resolve().parents[1]);
import os
# Ensure repo root is on sys.path for imports like app.xxx
sys.path.insert(0, p) if p not in sys.path else None

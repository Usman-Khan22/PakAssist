"""
Ensures the project root is on sys.path during test collection, so
`from backend...` imports resolve regardless of how/where pytest is
invoked (bare `pytest`, `py -m pytest`, from an IDE, etc.).
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
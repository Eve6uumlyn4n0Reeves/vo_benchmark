# Ensure backend root is on sys.path so that 'src' imports work in any environment
import os
import sys
from pathlib import Path

# tests/ is under backend/, so backend root is parent of this file's directory
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


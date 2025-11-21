import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / 'data' / 'raw'
DATA_PROCESSED = ROOT / 'data' / 'processed'
DB_PATH = ROOT / 'duckdb' / 'spatial_duck.db'


os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(DB_PATH.parent, exist_ok=True)

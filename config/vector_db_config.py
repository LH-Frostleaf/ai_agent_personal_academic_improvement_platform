import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = os.path.join(BASE_DIR, "storage", "vector_db")
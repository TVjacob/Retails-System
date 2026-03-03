import os
import json
from pathlib import Path

# ------------------------------------------------------------------
# Load env.json only if it exists (for local development)
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / "env.json"

def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            return json.load(f)
    return {}

env = load_env()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://postgres:password1@localhost:5432/retail_shop')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')

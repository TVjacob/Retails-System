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

# ------------------------------------------------------------------
# Final Config class – this works everywhere (local, Docker, Render)
# ------------------------------------------------------------------
class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://postgres:password1@localhost:5432/retail_shop')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # THIS IS THE ONLY LINE THAT MATTERS
    # Render injects DATABASE_URL automatically → we use it first
    # If not on Render → fall back to your env.json values
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")          # ← Render gives this (most important)
        or env.get("CLOUD_DB_URL")              # ← your Render DB string in env.json
        or env.get("DOCKER_DB_URL")             # ← for local docker-compose
        or env.get("LOCAL_DB_URL")              # ← for running locally without Docker
        or "postgresql://postgres:password1@localhost:5432/retail_db"
    )

    # Optional: make sure PostgreSQL driver is used (Render needs this format)
    # Render gives postgres://… but SQLAlchemy prefers postgresql://…
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
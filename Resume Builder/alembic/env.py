import sys
from pathlib import Path
import os  # <-- Added

sys.path.append(str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import the synchronous Base for Alembic
from app.core.sync_database import Base

# Import all models so they register with Base.metadata (critical for autogenerate!)
from app.models import *  # <-- This pulls in User, Resume, Subscription, Suggestion

# this is the Alembic Config object
config = context.config

# Setup Python logging from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------------
# Dynamic database URL - uses env var if available (Docker), else falls back to alembic.ini
# ------------------------------------------------------------------
# Priority:
# 1. ALEMBIC_DATABASE_URL env var (explicit override)
# 2. DATABASE_URL env var (common for runtime)
# 3. sqlalchemy.url from alembic.ini (fallback)
base_url = (
    os.getenv("ALEMBIC_DATABASE_URL") or
    os.getenv("DATABASE_URL") or
    config.get_main_option("sqlalchemy.url")
)

# Ensure correct host for Docker (resume-postgres instead of localhost)
# If the URL contains "localhost", replace with service name
if "localhost" in base_url:
    base_url = base_url.replace("localhost", "resume-postgres")

# Optional: force pg8000 for Alembic (sync driver)
if "asyncpg" in base_url:
    base_url = base_url.replace("postgresql+asyncpg", "postgresql+pg8000")

config.set_main_option("sqlalchemy.url", base_url)

# Print for debugging (very helpful)
print("ALEMBIC DATABASE URL:", base_url)

# Target metadata for 'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
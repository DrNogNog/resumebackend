# create_tables.py
from app.core.sync_database import Base, engine  # Base and engine must be sync
from app.db.models import User
from app.db.models import Resume  # if you have other models

def main():
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    main()
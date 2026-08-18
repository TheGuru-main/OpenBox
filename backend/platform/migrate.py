# migrate.py
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/openbox")

def run_migrations():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        with open("migrations/001_initial.sql") as f:
            sql = f.read()
        conn.execute(text(sql))
        conn.commit()
    print("Migration completed.")

if __name__ == "__main__":
    run_migrations()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/openbox")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
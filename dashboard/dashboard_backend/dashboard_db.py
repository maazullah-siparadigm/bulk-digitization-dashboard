import os
os.environ["DB_URL"] = os.environ["VIEWER_DB_URL"]
from LLMBatcher.executors.db.engine import create_engine_for_worker, create_sessionmaker

# Create ONE engine for API process
engine = create_engine_for_worker("fastapi-dashboard-backend")
SessionLocal = create_sessionmaker(engine)


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
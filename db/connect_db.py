import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the database URL from the environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    logger.error("DATABASE_URL is not set in environment variables.")
    raise EnvironmentError("DATABASE_URL is not set. Please set it in the .env file or environment variables.")

# Create the engine and sessionmaker
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optionally, create or drop the database schema
CREATE_SCHEMA = os.getenv("CREATE_SCHEMA", "False").lower() == "true"

if CREATE_SCHEMA:
    logger.info("Creating database schema...")
    Base.metadata.create_all(bind=engine)
else:
    logger.info("Skipping database schema creation.")


def get_db():
    """
    Dependency to get a database session. Closes the session when done.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: %s", e)
        raise
    finally:
        db.close()
        logger.info("Database session closed.")

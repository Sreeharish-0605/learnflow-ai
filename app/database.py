import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()
oracle_user = os.getenv("ORACLE_USER")
oracle_password = os.getenv("ORACLE_PASSWORD")
oracle_dsn = os.getenv("ORACLE_DSN")
wallet_dir = os.getenv("ORACLE_WALLET_DIR")

if oracle_user and oracle_password and oracle_dsn:
    DATABASE_URL = URL.create(
        "oracle+oracledb",
        username=oracle_user,
        password=oracle_password,
        host=oracle_dsn,
    )
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learnflow.db")

database_url_string = str(DATABASE_URL)
connect_args = {"check_same_thread": False} if database_url_string.startswith("sqlite") else {}
if database_url_string.startswith("oracle+") and wallet_dir:
    connect_args.update({"config_dir": wallet_dir, "wallet_location": wallet_dir})
    wallet_password = os.getenv("ORACLE_WALLET_PASSWORD")
    if wallet_password:
        connect_args["wallet_password"] = wallet_password
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

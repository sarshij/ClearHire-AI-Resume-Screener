import os
import hashlib
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, select
from sqlalchemy.sql import func
from app.logger import setup_logger

logger = setup_logger(__name__)

# Base model
Base = declarative_base()


# ── User Account Model ────────────────────────────────────────────────────────
class User(Base):
    """
    Stores registered HR and Applicant accounts.
    Passwords are stored as SHA-256 hex digests — no external dependency.
    """
    __tablename__ = 'users'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(80), nullable=False, unique=True, index=True)
    # SHA-256 hex hash of the password
    password_hash = Column(String(64), nullable=False)
    role       = Column(String(20), nullable=False, default='user')  # 'hr' or 'user'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def _hash_password(plaintext: str) -> str:
    """Return SHA-256 hex digest of the plaintext password."""
    return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()


async def create_user(session: AsyncSession, username: str, password: str, role: str) -> 'User | None':
    """
    Create a new user account.  Returns the User on success, None if username
    already exists.
    """
    # Check duplicate
    result = await session.execute(select(User).where(User.username == username.strip().lower()))
    if result.scalar_one_or_none():
        return None  # duplicate
    user = User(
        username=username.strip().lower(),
        password_hash=_hash_password(password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, username: str, password: str, role: str) -> bool:
    """
    Returns True if username+password+role match a DB record.
    """
    result = await session.execute(
        select(User).where(
            User.username == username.strip().lower(),
            User.password_hash == _hash_password(password),
            User.role == role,
        )
    )
    return result.scalar_one_or_none() is not None


class JobDescription(Base):
    __tablename__ = 'job_descriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ResumeAnalysis(Base):
    __tablename__ = 'resume_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=True)
    filename = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=True)
    
    # Core scores
    final_match_score = Column(Float, default=0.0)
    ai_plausibility_score = Column(Float, default=0.5)
    classification = Column(String(50), nullable=False)
    
    # JSON payload of all features/results for the frontend
    full_results = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ── PostgreSQL Connection ─────────────────────────────────────────────────────
# Priority: use DATABASE_URL directly if set, otherwise build from components.
# To switch between machines (e.g. dev → friend's laptop) simply update .env.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    pg_host     = os.environ.get("POSTGRES_HOST",     "localhost")
    pg_port     = os.environ.get("POSTGRES_PORT",     "5432")
    pg_db       = os.environ.get("POSTGRES_DB",       "resume_screener")
    pg_user     = os.environ.get("POSTGRES_USER",     "postgres")
    pg_password = os.environ.get("POSTGRES_PASSWORD", "")

    if not pg_password:
        logger.warning(
            "POSTGRES_PASSWORD is not set. "
            "Set it via the POSTGRES_PASSWORD environment variable or DATABASE_URL."
        )

    DATABASE_URL = (
        f"postgresql+asyncpg://{pg_user}:{pg_password}"
        f"@{pg_host}:{pg_port}/{pg_db}"
    )

# Async Engine and Session
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,   # detect dropped connections before using a pooled connection
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")

async def get_db():
    async with async_session() as session:
        yield session

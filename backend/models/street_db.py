import datetime
import os
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")
VIDEOS_DIR = os.path.join(UPLOADS_DIR, "videos")
THUMBNAILS_DIR = os.path.join(UPLOADS_DIR, "thumbnails")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

DB_PATH = os.path.join(BACKEND_DIR, "street.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    videos = relationship("StreetVideo", back_populates="uploader")
    watch_sessions = relationship("WatchSession", back_populates="user")


class StreetVideo(Base):
    __tablename__ = "street_videos"

    id = Column(Integer, primary_key=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploader = relationship("User", back_populates="videos")

    video_uuid = Column(String(64), unique=True, index=True, nullable=False, default=lambda: uuid.uuid4().hex)
    original_filename = Column(String(255), nullable=False)

    video_path = Column(String(512), nullable=False)  # relative to backend root (uploads/videos/...)
    thumbnail_path = Column(String(512), nullable=True)  # relative to backend root (uploads/thumbnails/...)

    status = Column(
        String(24),
        nullable=False,
        default="pending",
    )  # pending | approved | rejected
    moderation_reason = Column(Text, nullable=True)

    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    heading = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)


class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="watch_sessions")

    video_id = Column(Integer, ForeignKey("street_videos.id"), nullable=False)
    video = relationship("StreetVideo")

    report_token = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(24), nullable=False, default="active")  # active | ended

    last_reported_time_sec = Column(Float, nullable=False, default=0.0)
    accumulated_reported_seconds = Column(Float, nullable=False, default=0.0)
    accumulated_counted_seconds = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)


class PointsLedgerEvent(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("street_videos.id"), nullable=True)

    event_type = Column(
        String(48),
        nullable=False,
    )  # approved_upload | watch_time | penalty
    points = Column(Float, nullable=False)
    counted_seconds = Column(Float, nullable=True)

    meta_json = Column(Text, nullable=True)  # simple MVP: store serialized json string
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


def init_street_db() -> None:
    Base.metadata.create_all(bind=engine)


def utc_today_str() -> str:
    return datetime.datetime.utcnow().date().isoformat()


def sum_watch_seconds_today_for_user(db, *, user_id: int, video_id: int) -> float:
    today = utc_today_str()
    # SQLite date() works well enough for this MVP.
    q = (
        db.query(func.coalesce(func.sum(PointsLedgerEvent.counted_seconds), 0.0))
        .filter(PointsLedgerEvent.user_id == user_id)
        .filter(PointsLedgerEvent.event_type == "watch_time")
        .filter(PointsLedgerEvent.video_id == video_id)
        .filter(func.date(PointsLedgerEvent.created_at) == today)
    )
    return float(q.scalar() or 0.0)


def sum_watch_seconds_today_for_user_all_videos(db, *, user_id: int) -> float:
    today = utc_today_str()
    q = (
        db.query(func.coalesce(func.sum(PointsLedgerEvent.counted_seconds), 0.0))
        .filter(PointsLedgerEvent.user_id == user_id)
        .filter(PointsLedgerEvent.event_type == "watch_time")
        .filter(func.date(PointsLedgerEvent.created_at) == today)
    )
    return float(q.scalar() or 0.0)


def get_user_points(db, *, user_id: int) -> float:
    q = (
        db.query(func.coalesce(func.sum(PointsLedgerEvent.points), 0.0))
        .filter(PointsLedgerEvent.user_id == user_id)
    )
    return float(q.scalar() or 0.0)


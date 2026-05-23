import datetime
import os
import uuid
from typing import Optional

import cv2
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.street_db import (
    SessionLocal,
    StreetVideo,
    PointsLedgerEvent,
    User,
    WatchSession,
    init_street_db,
    sum_watch_seconds_today_for_user,
    sum_watch_seconds_today_for_user_all_videos,
    get_user_points,
)
from utils.street_auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

APPROVED_UPLOAD_POINTS = 100.0
POINTS_PER_SECOND = 0.2  # 2 points per 10 seconds

MIN_SECONDS_BEFORE_COUNTING = 15.0  # “continuous” proxy (session-level threshold)
MAX_COUNTED_SECONDS_PER_VIDEO_PER_DAY = 20.0 * 60.0
MAX_COUNTED_SECONDS_PER_USER_PER_DAY = 120.0 * 60.0

MAX_DELTA_SECONDS_PER_REPORT = 10.0
MAX_ACCEPTED_TIME_SKEW_SECONDS = 60.0 * 60.0  # 1h (client time sec is usually 0..duration)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LevelResponse(BaseModel):
    points: float
    level: str
    watched_today_seconds: float


@router.on_event("startup")
def _init_db_on_startup() -> None:
    init_street_db()


def level_from_points(points: float) -> str:
    if points < 500:
        return "New Contributor"
    if points < 2000:
        return "Street Scout"
    if points < 5000:
        return "Route Mapper"
    return "Verified Lens"


def relative_video_url(video_path_rel: str) -> str:
    # video_path_rel is like uploads/videos/<filename>. The backend serves under /uploads.
    # Keep it simple: just strip leading `uploads/`.
    # Example: uploads/videos/abc.mp4 -> /uploads/videos/abc.mp4
    if video_path_rel.startswith("uploads/"):
        return "/" + video_path_rel
    return "/uploads/" + video_path_rel


def relative_thumb_url(thumb_path_rel: Optional[str]) -> Optional[str]:
    if not thumb_path_rel:
        return None
    if thumb_path_rel.startswith("uploads/"):
        return "/" + thumb_path_rel
    return "/uploads/" + thumb_path_rel


def video_storage_abs_path(video_path_rel: str) -> str:
    # backend/models/street_db.py created it relative to backend root.
    # video_path_rel: uploads/videos/<filename>
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(backend_dir, video_path_rel)


def thumb_storage_abs_path(thumb_path_rel: str) -> str:
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(backend_dir, thumb_path_rel)


def generate_thumbnail(video_id: int, *, video_path_rel: str, thumb_path_rel: str) -> None:
    abs_video_path = video_storage_abs_path(video_path_rel)
    abs_thumb_path = thumb_storage_abs_path(thumb_path_rel)

    cap = cv2.VideoCapture(abs_video_path)
    try:
        if not cap.isOpened():
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        # Take a frame around 1 second (or fallback to frame 0)
        target_frame = int(max(0, fps) * 1.0) if fps > 0 else 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        ret, frame = cap.read()
        if not ret:
            # Fallback: seek to the middle-ish
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                return

        os.makedirs(os.path.dirname(abs_thumb_path), exist_ok=True)
        cv2.imwrite(abs_thumb_path, frame)
    finally:
        cap.release()

    # Update db
    db = SessionLocal()
    try:
        video = db.query(StreetVideo).filter(StreetVideo.id == video_id).first()
        if video:
            video.thumbnail_path = thumb_path_rel
            video.updated_at = datetime.datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.post("/auth/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    is_first_user = db.query(User).count() == 0
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=is_first_user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "username": user.username}


@router.post("/auth/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.username == form.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"id": current_user.id, "username": current_user.username, "is_admin": current_user.is_admin}


@router.get("/me/points", response_model=LevelResponse)
def me_points(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> LevelResponse:
    points = get_user_points(db, user_id=current_user.id)
    return LevelResponse(
        points=points,
        level=level_from_points(points),
        watched_today_seconds=sum_watch_seconds_today_for_user_all_videos(db, user_id=current_user.id),
    )


@router.post("/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
    heading: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    video_uuid = uuid.uuid4().hex
    ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    safe_name = f"{video_uuid}{ext}"

    video_path_rel = os.path.join("uploads", "videos", safe_name)
    thumb_path_rel = os.path.join("uploads", "thumbnails", f"{video_uuid}.jpg")

    abs_video_path = video_storage_abs_path(video_path_rel)
    os.makedirs(os.path.dirname(abs_video_path), exist_ok=True)

    # Store file to disk
    with open(abs_video_path, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    video = StreetVideo(
        uploader_id=current_user.id,
        video_uuid=video_uuid,
        original_filename=file.filename,
        video_path=video_path_rel,
        thumbnail_path=None,
        status="pending",
        lat=lat,
        lng=lng,
        heading=heading,
        duration_seconds=None,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Generate thumbnail async so request returns quickly.
    background_tasks.add_task(
        generate_thumbnail,
        video.id,
        video_path_rel=video_path_rel,
        thumb_path_rel=thumb_path_rel,
    )

    return {"video_id": video.id, "status": video.status}


class ModerationDecision(BaseModel):
    reason: Optional[str] = None


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.post("/moderation/videos/{video_id}/approve")
def approve_video(
    video_id: int,
    payload: ModerationDecision | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin(current_user)
    video = db.query(StreetVideo).filter(StreetVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status == "approved":
        return {"status": "already_approved"}
    if video.status == "rejected":
        raise HTTPException(status_code=409, detail="Rejected videos cannot be approved in MVP")

    video.status = "approved"
    video.approved_at = datetime.datetime.utcnow()
    video.updated_at = datetime.datetime.utcnow()
    db.commit()

    # Award points once on approval.
    ledger = PointsLedgerEvent(
        user_id=video.uploader_id,
        video_id=video.id,
        event_type="approved_upload",
        points=APPROVED_UPLOAD_POINTS,
        counted_seconds=None,
        meta_json=None,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(ledger)
    db.commit()

    return {"status": "approved"}


@router.post("/moderation/videos/{video_id}/reject")
def reject_video(
    video_id: int,
    payload: ModerationDecision | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_admin(current_user)
    video = db.query(StreetVideo).filter(StreetVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status == "approved":
        raise HTTPException(status_code=409, detail="Approved videos cannot be rejected in MVP")

    video.status = "rejected"
    video.rejected_at = datetime.datetime.utcnow()
    video.moderation_reason = payload.reason if payload and payload.reason else None
    video.updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "rejected"}


@router.get("/map/videos")
def map_videos(
    minLat: float,
    minLng: float,
    maxLat: float,
    maxLng: float,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    if limit < 1 or limit > 200:
        limit = 50

    videos = (
        db.query(StreetVideo)
        .filter(StreetVideo.status == "approved")
        .filter(StreetVideo.lat >= minLat)
        .filter(StreetVideo.lat <= maxLat)
        .filter(StreetVideo.lng >= minLng)
        .filter(StreetVideo.lng <= maxLng)
        .order_by(StreetVideo.created_at.desc())
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": v.id,
            "lat": v.lat,
            "lng": v.lng,
            "heading": v.heading,
            "thumbnail_url": relative_thumb_url(v.thumbnail_path),
            "video_url": relative_video_url(v.video_path),
            "uploader_username": v.uploader.username if v.uploader else None,
        }
        for v in videos
    ]

    return {"items": items}


@router.get("/videos/{video_id}")
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
) -> dict:
    video = db.query(StreetVideo).filter(StreetVideo.id == video_id).first()
    if not video or video.status != "approved":
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "id": video.id,
        "lat": video.lat,
        "lng": video.lng,
        "heading": video.heading,
        "thumbnail_url": relative_thumb_url(video.thumbnail_path),
        "video_url": relative_video_url(video.video_path),
        "uploader_username": video.uploader.username if video.uploader else None,
    }


@router.post("/watch/videos/{video_id}/session/start")
def start_watch_session(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    video = db.query(StreetVideo).filter(StreetVideo.id == video_id).first()
    if not video or video.status != "approved":
        raise HTTPException(status_code=404, detail="Video not found")

    token = uuid.uuid4().hex
    session = WatchSession(
        user_id=current_user.id,
        video_id=video.id,
        report_token=token,
        status="active",
        last_reported_time_sec=0.0,
        accumulated_reported_seconds=0.0,
        accumulated_counted_seconds=0.0,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"watch_session_id": session.id, "report_token": session.report_token}


class WatchReport(BaseModel):
    watch_session_id: int
    report_token: str
    clientVideoTimeSec: float = Field(ge=0)
    isPlaying: bool = True


@router.post("/watch/videos/{video_id}/session/report")
def report_watch_time(
    video_id: int,
    payload: WatchReport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = db.query(WatchSession).filter(WatchSession.id == payload.watch_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Watch session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")
    if session.report_token != payload.report_token:
        raise HTTPException(status_code=401, detail="Invalid report token")
    if session.video_id != video_id:
        raise HTTPException(status_code=400, detail="Video mismatch")
    if session.status != "active":
        return {"counted_seconds": 0.0, "points_awarded": 0.0}

    now = datetime.datetime.utcnow()
    client_time = float(payload.clientVideoTimeSec)
    if client_time > MAX_ACCEPTED_TIME_SKEW_SECONDS:
        raise HTTPException(status_code=400, detail="Invalid client time")

    delta = client_time - float(session.last_reported_time_sec)
    if delta < 0:
        # client seeking backwards; ignore without counting points
        delta = 0.0

    delta = min(delta, MAX_DELTA_SECONDS_PER_REPORT)

    # Always advance last_reported_time_sec so “resume” doesn't count wrongly.
    session.last_reported_time_sec = client_time

    counted_seconds = 0.0
    points_awarded = 0.0
    if payload.isPlaying and delta > 0:
        # Only accumulate toward the “start counting” threshold while playing.
        before = float(session.accumulated_reported_seconds)
        after = before + delta
        session.accumulated_reported_seconds = after

        # Continuous threshold proxy: only start counting after MIN_SECONDS total *playing* seconds.
        if after >= MIN_SECONDS_BEFORE_COUNTING:
            needed = max(MIN_SECONDS_BEFORE_COUNTING - before, 0.0)
            counted_seconds = max(0.0, delta - needed)

        # Apply per-day caps.
        if counted_seconds > 0:
            already_video = sum_watch_seconds_today_for_user(
                db,
                user_id=current_user.id,
                video_id=video_id,
            )
            already_user = sum_watch_seconds_today_for_user_all_videos(db, user_id=current_user.id)

            remaining_video = MAX_COUNTED_SECONDS_PER_VIDEO_PER_DAY - already_video
            remaining_user = MAX_COUNTED_SECONDS_PER_USER_PER_DAY - already_user
            allowed = min(counted_seconds, remaining_video, remaining_user)
            counted_seconds = max(0.0, allowed)

            points_awarded = counted_seconds * POINTS_PER_SECOND

            if points_awarded > 0:
                ledger = PointsLedgerEvent(
                    user_id=current_user.id,
                    video_id=video_id,
                    event_type="watch_time",
                    points=points_awarded,
                    counted_seconds=counted_seconds,
                    meta_json=None,
                    created_at=now,
                )
                db.add(ledger)
                session.accumulated_counted_seconds = float(
                    session.accumulated_counted_seconds + counted_seconds
                )

    db.commit()
    return {"counted_seconds": counted_seconds, "points_awarded": points_awarded}


@router.post("/watch/videos/{video_id}/session/end")
def end_watch_session(
    video_id: int,
    watch_session_id: int = Form(...),
    report_token: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = db.query(WatchSession).filter(WatchSession.id == watch_session_id).first()
    if not session:
        return {"status": "no_session"}
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")
    if session.report_token != report_token:
        raise HTTPException(status_code=401, detail="Invalid report token")
    if session.video_id != video_id:
        raise HTTPException(status_code=400, detail="Video mismatch")

    session.status = "ended"
    session.ended_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "ended"}


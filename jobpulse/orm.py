"""
SQLAlchemy ORM layer for JobPulse application.
Handles database connections and data models for app config, user profiles, and job data.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

# Database engine and session - module-level singletons
_engine = None
_SessionLocal = None


# ============================================================================
# Database Models
# ============================================================================


class AppConfig(Base):
    """Application-level configuration settings."""

    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    """User profile and preferences."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True)
    phone = Column(String(20))
    location = Column(String(100))
    preferred_job_type = Column(String(50))
    preferred_job_level = Column(String(50))
    min_salary = Column(Float)
    max_salary = Column(Float)
    keywords = Column(Text)  # Comma-separated keywords
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job_applications = relationship("JobApplication", back_populates="profile")


class Job(Base):
    """Job listing information."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True)  # ID from job site
    title = Column(String(255), nullable=False)
    company = Column(String(200))
    location = Column(String(100))
    job_type = Column(String(50))
    job_level = Column(String(50))
    salary_range = Column(String(100))
    experience_required = Column(String(100))
    description = Column(Text)
    requirements = Column(Text)
    posted_date = Column(DateTime)
    deadline = Column(DateTime)
    url = Column(String(500))
    source = Column(String(50))  # e.g., "bdjobs", "linkedin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = relationship("JobApplication", back_populates="job")


class JobApplication(Base):
    """Track job applications and their status."""

    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), default="interested")  # interested, applied, interview, rejected, accepted
    applied_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="job_applications")
    job = relationship("Job", back_populates="applications")


# ============================================================================
# Database Connection Management
# ============================================================================


def init_database(connection_string: Optional[str] = None) -> None:
    """
    Initialize database connection and create tables.

    Args:
        connection_string: SQLAlchemy connection string.
                          Defaults to SQLite in user's home directory.
    """
    global _engine, _SessionLocal

    if connection_string is None:
        # db_path = Path.home() / ".jobpulse" / "jobpulse.db"
        # current root
        db_path = Path(__file__).parent.parent / "jobpulse.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection_string = f"sqlite:///{db_path}"

    _engine = create_engine(connection_string, echo=False)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

    # Create all tables
    Base.metadata.create_all(bind=_engine)
    logger.info(f"Database initialized: {connection_string}")


def get_session():
    """Get a new database session."""
    if _SessionLocal is None:
        init_database()
    return _SessionLocal()


def close_database() -> None:
    """Close database connection."""
    global _engine
    if _engine:
        _engine.dispose()
        logger.info("Database connection closed")


# ============================================================================
# Config Management Functions
# ============================================================================


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value by key."""
    session = get_session()
    try:
        config = session.query(AppConfig).filter_by(key=key).first()
        return config.value if config else default
    finally:
        session.close()


def set_config(key: str, value: Any, description: str = "") -> None:
    """Set configuration value."""
    session = get_session()
    try:
        config = session.query(AppConfig).filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.updated_at = datetime.utcnow()
            if description:
                config.description = description
        else:
            config = AppConfig(key=key, value=str(value), description=description)
            session.add(config)
        session.commit()
    finally:
        session.close()


def get_all_configs() -> Dict[str, str]:
    """Get all configuration key-value pairs."""
    session = get_session()
    try:
        configs = session.query(AppConfig).all()
        return {config.key: config.value for config in configs}
    finally:
        session.close()


# ============================================================================
# User Profile Functions
# ============================================================================


def create_profile(profile_data: Dict[str, Any]) -> int:
    """Create a new user profile."""
    session = get_session()
    try:
        profile = UserProfile(**profile_data)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile.id
    finally:
        session.close()


def get_profile(profile_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile by ID."""
    session = get_session()
    try:
        profile = session.query(UserProfile).filter_by(id=profile_id).first()
        if profile:
            return {
                "id": profile.id,
                "name": profile.name,
                "email": profile.email,
                "phone": profile.phone,
                "location": profile.location,
                "preferred_job_type": profile.preferred_job_type,
                "preferred_job_level": profile.preferred_job_level,
                "min_salary": profile.min_salary,
                "max_salary": profile.max_salary,
                "keywords": profile.keywords,
                "is_active": profile.is_active,
            }
        return None
    finally:
        session.close()


def get_all_profiles() -> List[Dict[str, Any]]:
    """Get all user profiles."""
    session = get_session()
    try:
        profiles = session.query(UserProfile).filter_by(is_active=True).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "location": p.location,
            }
            for p in profiles
        ]
    finally:
        session.close()


def update_profile(profile_id: int, profile_data: Dict[str, Any]) -> bool:
    """Update user profile."""
    session = get_session()
    try:
        profile = session.query(UserProfile).filter_by(id=profile_id).first()
        if profile:
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False
    finally:
        session.close()


def delete_profile(profile_id: int) -> bool:
    """Soft delete user profile."""
    session = get_session()
    try:
        profile = session.query(UserProfile).filter_by(id=profile_id).first()
        if profile:
            profile.is_active = False
            profile.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False
    finally:
        session.close()


# ============================================================================
# Job Data Functions
# ============================================================================


def save_job(job_data: Dict[str, Any]) -> int:
    """Save or update a job listing."""
    session = get_session()
    try:
        external_id = job_data.get("external_id")
        job = None

        if external_id:
            job = session.query(Job).filter_by(external_id=external_id).first()

        if job:
            # Update existing job
            for key, value in job_data.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.utcnow()
        else:
            # Create new job
            job = Job(**job_data)
            session.add(job)

        session.commit()
        session.refresh(job)
        return job.id
    finally:
        session.close()


def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get job by ID."""
    session = get_session()
    try:
        job = session.query(Job).filter_by(id=job_id).first()
        if job:
            return {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "salary_range": job.salary_range,
                "description": job.description,
                "url": job.url,
                "posted_date": job.posted_date,
                "deadline": job.deadline,
            }
        return None
    finally:
        session.close()


def search_jobs(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search jobs with filters."""
    session = get_session()
    try:
        query = session.query(Job).filter_by(is_active=True)

        if "keyword" in filters:
            keyword = f"%{filters['keyword']}%"
            query = query.filter((Job.title.like(keyword)) | (Job.description.like(keyword)))

        if "location" in filters:
            query = query.filter(Job.location.like(f"%{filters['location']}%"))

        if "job_type" in filters:
            query = query.filter_by(job_type=filters["job_type"])

        jobs = query.order_by(Job.posted_date.desc()).limit(100).all()

        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_range": job.salary_range,
                "posted_date": job.posted_date,
                "url": job.url,
            }
            for job in jobs
        ]
    finally:
        session.close()


# ============================================================================
# Job Application Functions
# ============================================================================


def create_application(profile_id: int, job_id: int, status: str = "interested", notes: str = "") -> int:
    """Create a job application record."""
    session = get_session()
    try:
        application = JobApplication(
            profile_id=profile_id,
            job_id=job_id,
            status=status,
            notes=notes,
        )
        session.add(application)
        session.commit()
        session.refresh(application)
        return application.id
    finally:
        session.close()


def update_application_status(application_id: int, status: str, notes: str = "") -> bool:
    """Update job application status."""
    session = get_session()
    try:
        application = session.query(JobApplication).filter_by(id=application_id).first()
        if application:
            application.status = status
            if notes:
                application.notes = notes
            application.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_applications_for_profile(profile_id: int) -> List[Dict[str, Any]]:
    """Get all applications for a profile."""
    session = get_session()
    try:
        applications = (
            session.query(JobApplication)
            .filter_by(profile_id=profile_id)
            .order_by(JobApplication.created_at.desc())
            .all()
        )

        return [
            {
                "id": app.id,
                "job_id": app.job_id,
                "status": app.status,
                "applied_date": app.applied_date,
                "notes": app.notes,
            }
            for app in applications
        ]
    finally:
        session.close()

"""SQLAlchemy models for Salarite."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

def utc_now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    display_name = Column(String(100), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, index=True)  # employer | virtual_hr
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, default="", nullable=False)
    status = Column(String(30), default="assigned", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    category = Column(String(60), default="HR Operations", nullable=False)
    completion_criteria = Column(Text, default="", nullable=False)
    blocker_reason = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    assignee = relationship("User", foreign_keys=[assignee_id])
    activities = relationship("TaskActivity", back_populates="task", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_task_status_due", "status", "due_at"),)

class TaskActivity(Base):
    __tablename__ = "task_activities"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(60), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    task = relationship("Task", back_populates="activities")
    actor = relationship("User")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(120), nullable=False)
    candidate_email = Column(String(180), nullable=True)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    mode = Column(String(20), nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    timezone = Column(String(60), default="Asia/Kolkata", nullable=False)
    status = Column(String(20), default="scheduled", nullable=False)
    meeting_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    interviewer = relationship("User")

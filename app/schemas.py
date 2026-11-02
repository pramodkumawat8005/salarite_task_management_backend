from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
Status = Literal["assigned", "in_progress", "blocked", "completed", "cancelled"]
Priority = Literal["low", "medium", "high", "urgent"]
Mode = Literal["voice", "video", "chat"]
class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=5000)
    priority: Priority = "medium"
    category: str = Field(default="Recruitment", max_length=60)
    completion_criteria: str = Field(default="", max_length=3000)
    due_at: Optional[datetime] = None
    assignee_id: int
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=160)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[Priority] = None
    category: Optional[str] = Field(default=None, max_length=60)
    completion_criteria: Optional[str] = Field(default=None, max_length=3000)
    due_at: Optional[datetime] = None
    assignee_id: Optional[int] = None
class StatusUpdate(BaseModel):
    status: Status
    note: Optional[str] = Field(default=None, max_length=2000)
    blocker_reason: Optional[str] = Field(default=None, max_length=2000)
class ProgressUpdate(BaseModel):
    progress: int = Field(ge=0, le=99)
    note: Optional[str] = Field(default=None, max_length=2000)
class InterviewCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=120)
    candidate_email: Optional[str] = None
    related_task_id: Optional[int] = None
    mode: Mode
    scheduled_start: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    timezone: str = "Asia/Kolkata"
    meeting_url: Optional[str] = None
    notes: Optional[str] = None
class CancelInterview(BaseModel): 
    reason: str = Field(min_length=2, max_length=1000)
class ORMModel(BaseModel): 
    model_config = ConfigDict(from_attributes=True)
class UserOut(ORMModel): 
    id: int; 
    display_name: str; 
    email: str; 
    role: str
class ActivityOut(ORMModel):
    id: int; 
    task_id: int; 
    actor_id: int; 
    event_type: str; 
    old_value: Optional[str]; 
    new_value: Optional[str]; 
    note: Optional[str]; 
    created_at: datetime; 
    actor: Optional[UserOut] = None
class TaskOut(ORMModel):
    id: int; 
    title: str; 
    description: str; 
    status: str; 
    priority: str; 
    progress: int; 
    category: str; 
    completion_criteria: str; 
    blocker_reason: Optional[str]; 
    due_at: Optional[datetime]; 
    assignee_id: int; 
    created_by_id: int; 
    created_at: datetime; 
    updated_at: datetime; 
    completed_at: Optional[datetime]; 
    assignee: Optional[UserOut] = None
class TaskDetail(TaskOut): 
    activities: list[ActivityOut] = []
class InterviewOut(ORMModel):
    id: int; 
    candidate_name: str; 
    candidate_email: Optional[str]; 
    interviewer_id: int; 
    related_task_id: Optional[int]; 
    mode: str; 
    scheduled_start: datetime; 
    duration_minutes: int; 
    timezone: str; 
    status: str; 
    meeting_url: Optional[str]; 
    notes: Optional[str]; 
    created_at: datetime; 
    updated_at: datetime; 
    interviewer: Optional[UserOut] = None

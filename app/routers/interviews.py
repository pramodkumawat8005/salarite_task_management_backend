"""HR schedules interviews; every authenticated role can view the schedule."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas
from ..security import current_user, require_role
router=APIRouter(prefix="/api/interviews",tags=["Interviews"])
@router.get("",response_model=list[schemas.InterviewOut])
def list_interviews(status:str|None=None,mode:str|None=None,db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    q=db.query(models.Interview).options(joinedload(models.Interview.interviewer))
    if status:
        q=q.filter(models.Interview.status==status)
    if mode:
        q=q.filter(models.Interview.mode==mode)
    return q.order_by(models.Interview.scheduled_start.asc()).all()

@router.post("",response_model=schemas.InterviewOut,status_code=201)
def create_interview(payload:schemas.InterviewCreate,db:Session=Depends(get_db),user:models.User=Depends(require_role("virtual_hr"))):
    if payload.related_task_id:
        task=db.query(models.Task).filter(models.Task.id==payload.related_task_id).first()
        if not task:raise HTTPException(422,"Related task does not exist.")
        if task.assignee_id!=user.id:
            raise HTTPException(403,"You can only schedule interviews related to your assigned tasks.")
    if payload.scheduled_start.tzinfo is None:
        raise HTTPException(422,"Choose a valid date/time with timezone.")
    if payload.scheduled_start <= datetime.now(timezone.utc):
        raise HTTPException(422,"Interview must be scheduled in the future.")
    if not payload.meeting_url:
        raise HTTPException(422,"Add a meeting/call link so participants can join.")
    row=models.Interview(**payload.model_dump(),interviewer_id=user.id,status="scheduled")
    db.add(row);
    db.commit();
    db.refresh(row);
    return row

@router.post("/{interview_id}/cancel",response_model=schemas.InterviewOut)
def cancel_interview(interview_id:int,payload:schemas.CancelInterview,db:Session=Depends(get_db),user:models.User=Depends(require_role("virtual_hr"))):
    row=db.query(models.Interview).options(joinedload(models.Interview.interviewer)).filter(models.Interview.id==interview_id).first()
    if not row:
        raise HTTPException(404,"Interview not found.")
    if row.interviewer_id!=user.id:
        raise HTTPException(403,"Only the HR who scheduled this interview can cancel it.")
    if row.status=="completed":
        raise HTTPException(409,"Completed interviews cannot be cancelled.")
    row.status="cancelled";row.notes=(row.notes or "")+f"\nCancellation reason: {payload.reason}";row.updated_at=datetime.now(timezone.utc)
    db.commit();
    db.refresh(row);
    return row

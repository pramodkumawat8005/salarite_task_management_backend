"""Task CRUD with role-aware access: employers manage tasks, HR updates assigned work."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas
from ..security import current_user, require_role
router = APIRouter(prefix="/api", tags=["Tasks"])
TRANSITIONS={"assigned":{"in_progress","blocked","cancelled"},
             "in_progress":{"blocked","completed","cancelled"},
             "blocked":{"in_progress","cancelled"},
             "completed":set(),"cancelled":set()}
def record_activity(db, task_id, actor_id, event, old=None, new=None, note=None):
    db.add(models.TaskActivity(task_id=task_id, actor_id=actor_id, event_type=event, old_value=old, new_value=new, note=note))

def get_task(db, task_id):
    task=db.query(models.Task).options(joinedload(models.Task.assignee)).filter(models.Task.id==task_id).first()
    if not task: raise HTTPException(404,"Task not found.")
    return task

def overdue(t):
    if not t.due_at or t.status in {"completed","cancelled"}: return False
    due=t.due_at if t.due_at.tzinfo else t.due_at.replace(tzinfo=timezone.utc)
    return due < datetime.now(timezone.utc)

@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db:Session=Depends(get_db), user:models.User=Depends(current_user)):
    return db.query(models.User).filter(models.User.role=="virtual_hr").order_by(models.User.display_name).all()

@router.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(status:str|None=None, priority:str|None=None, search:str|None=Query(default=None,max_length=100), assignee_id:int|None=None, db:Session=Depends(get_db), user:models.User=Depends(current_user)):
    q=db.query(models.Task).options(joinedload(models.Task.assignee))
    if user.role=="virtual_hr": 
        q=q.filter(models.Task.assignee_id==user.id)
    if status: 
        q=q.filter(models.Task.status==status)
    if priority: 
        q=q.filter(models.Task.priority==priority)
    if assignee_id and user.role=="employer": 
        q=q.filter(models.Task.assignee_id==assignee_id)
    if user.role == "employer":
        q = q.filter(models.Task.created_by_id == user.id)    
    if search:
        term=f"%{search.strip()}%"; 
        q=q.filter(or_(models.Task.title.ilike(term),models.Task.description.ilike(term)))
    return q.order_by(models.Task.updated_at.desc()).all()

@router.post("/tasks", response_model=schemas.TaskOut,status_code=201)
def create_task(payload:schemas.TaskCreate, db:Session=Depends(get_db), user:models.User=Depends(require_role("employer"))):
    assignee=db.query(models.User).filter(models.User.id==payload.assignee_id,models.User.role=="virtual_hr").first()
    if not assignee: 
        raise HTTPException(422,"Choose a valid HR account to assign this task.")
    task=models.Task(**payload.model_dump(),created_by_id=user.id,status="assigned",progress=0)
    db.add(task); 
    db.flush(); 
    record_activity(db,task.id,user.id,"task_created",new="assigned",note="Task created and assigned.")
    db.commit(); 
    db.refresh(task); 
    return task

@router.get("/tasks/{task_id}",response_model=schemas.TaskDetail)
def task_detail(task_id:int,db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    task=db.query(models.Task).options(joinedload(models.Task.assignee),joinedload(models.Task.activities).joinedload(models.TaskActivity.actor)).filter(models.Task.id==task_id).first()
    if not task: 
        raise HTTPException(404,"Task not found.")
    if user.role=="virtual_hr" and task.assignee_id!=user.id: 
        raise HTTPException(403,"This task is assigned to another HR account.")
    return task

@router.patch("/tasks/{task_id}",response_model=schemas.TaskOut)
def edit_task(task_id:int,payload:schemas.TaskUpdate,db:Session=Depends(get_db),user:models.User=Depends(require_role("employer"))):
    task=get_task(db,task_id); data=payload.model_dump(exclude_unset=True)
    if "assignee_id" in data:
        assignee=db.query(models.User).filter(models.User.id==data["assignee_id"],models.User.role=="virtual_hr").first()
        if not assignee: 
            raise HTTPException(422,"Choose a valid HR account.")
    for key,value in data.items(): 
        setattr(task,key,value)
    task.updated_at=datetime.now(timezone.utc); 
    record_activity(db,task.id,user.id,"task_edited",note="Task details edited by employer.")
    db.commit(); 
    db.refresh(task);
    return task

@router.delete("/tasks/{task_id}",status_code=204)
def delete_task(task_id:int,db:Session=Depends(get_db),user:models.User=Depends(require_role("employer"))):
    task=db.query(models.Task).filter(models.Task.id==task_id).first()
    if not task: 
        raise HTTPException(404,"Task not found.")
    db.delete(task); db.commit(); return None

@router.post("/tasks/{task_id}/status",response_model=schemas.TaskOut)
def update_status(task_id:int,payload:schemas.StatusUpdate,db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    task=get_task(db,task_id)
    if user.role=="virtual_hr" and task.assignee_id!=user.id: 
        raise HTTPException(403,"You can only update your assigned tasks.")
    if user.role=="employer": 
        raise HTTPException(403,"Employers manage task details; HR updates task progress and status.")
    if payload.status==task.status:
        return task
    if payload.status not in TRANSITIONS[task.status]:
        raise HTTPException(409,f"Transition from {task.status} to {payload.status} is not allowed.")
    if payload.status=="blocked" and not (payload.blocker_reason or "").strip():
        raise HTTPException(422,"A blocker reason is required.")
    old=task.status; task.status=payload.status
    if payload.status=="completed":
        task.progress=100;task.completed_at=datetime.now(timezone.utc)
    elif payload.status=="in_progress" and task.progress==0:
        task.progress=1
    task.blocker_reason=payload.blocker_reason.strip() if payload.status=="blocked" else None; task.updated_at=datetime.now(timezone.utc)
    record_activity(db,task.id,user.id,"status_changed",old,task.status,payload.note);
    db.commit();
    db.refresh(task);
    return task

@router.post("/tasks/{task_id}/progress",response_model=schemas.TaskOut)
def update_progress(task_id:int,payload:schemas.ProgressUpdate,db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    task=get_task(db,task_id)
    if user.role!="virtual_hr" or task.assignee_id!=user.id:
        raise HTTPException(403,"Only the assigned HR can update progress.")
    if task.status in {"completed","cancelled"}:
        raise HTTPException(409,"This task is closed.")
    old=task.progress;task.progress=payload.progress
    if payload.progress>0 and task.status=="assigned":
        task.status="in_progress"
    task.updated_at=datetime.now(timezone.utc);
    record_activity(db,task.id,user.id,"progress_updated",str(old),str(task.progress),payload.note);
    db.commit();
    db.refresh(task);
    return task

@router.get("/dashboard/summary")
def dashboard_summary(db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    q=db.query(models.Task)
    if user.role=="virtual_hr":
        q=q.filter(models.Task.assignee_id==user.id)
    tasks=q.all(); 

    iq=db.query(models.Interview).options(joinedload(models.Interview.interviewer)).filter(models.Interview.status=="scheduled")

    interviews=iq.order_by(models.Interview.scheduled_start.asc()).limit(8).all()
    
    counts={s:sum(t.status==s for t in tasks) for s in ["assigned","in_progress","blocked","completed","cancelled"]}
    aq=db.query(models.TaskActivity).options(joinedload(models.TaskActivity.actor),joinedload(models.TaskActivity.task))
    if user.role=="virtual_hr":
        aq=aq.join(models.Task,models.Task.id==models.TaskActivity.task_id).filter(models.Task.assignee_id==user.id)
    activity=aq.order_by(models.TaskActivity.created_at.desc()).limit(8).all()
    return {"total":len(tasks),"overdue":sum(overdue(t) for t in tasks),"counts":counts,"upcoming_interviews":interviews,"recent_activity":[{"id":a.id,"task_id":a.task_id,"task_title":a.task.title,"actor_name":a.actor.display_name,"event_type":a.event_type,"note":a.note,"created_at":a.created_at} for a in activity]}

@router.get("/activity")
def activity_feed(limit:int=Query(30,ge=1,le=100),db:Session=Depends(get_db),user:models.User=Depends(current_user)):
    q=db.query(models.TaskActivity).options(joinedload(models.TaskActivity.actor),joinedload(models.TaskActivity.task))
    if user.role=="virtual_hr":
        q=q.join(models.Task,models.Task.id==models.TaskActivity.task_id).filter(models.Task.assignee_id==user.id)
    rows=q.order_by(models.TaskActivity.created_at.desc()).limit(limit).all()
    return [{"id":a.id,"task_id":a.task_id,"task_title":a.task.title,"actor_name":a.actor.display_name,"event_type":a.event_type,"note":a.note,"created_at":a.created_at} for a in rows]

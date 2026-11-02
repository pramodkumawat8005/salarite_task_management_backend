from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import auth, interviews, tasks

Base.metadata.create_all(bind=engine)

app=FastAPI(title="Salarite HR Workspace API",version="2.0.0",description="JWT-authenticated task management and interview scheduling.")

origins=[x.strip() for x in os.getenv("FRONTEND_ORIGIN","https://salarite-task-management-frontend.vercel.app").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["GET","POST","PATCH","PUT","DELETE","OPTIONS"],allow_headers=["*"])

@app.get("/health",tags=["Health"])

def health():return {"status":"ok","service":"salarite-hr-api","version":app.version}

app.include_router(auth.router);
app.include_router(tasks.router);
app.include_router(interviews.router)

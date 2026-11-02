# Salarite — Role-based HR Task & Interview Workspace

Full-stack MVP built with **FastAPI, SQLAlchemy, SQLite, Next.js, React and TypeScript**. The app now has real registration/login with JWT bearer tokens and server-side role/ownership checks.

## Roles and permissions
- **Employer:** sees workspace tasks and the shared interview schedule; creates, edits, assigns and deletes tasks; tracks progress and activity.
- **HR:** sees only tasks assigned to their account; updates task progress/status and blocker reasons; schedules/cancels their interviews.
- **Both roles:** can view the full interview schedule and use the Join link when a meeting/call URL is provided.
- Role permissions are enforced by the API, not just hidden UI controls.

## Features
- Professional responsive sign-in and registration UI, role selection, password visibility toggle, field validation and clear error states.
- JWT access tokens (12-hour expiry), password hashing, `/api/auth/me` session validation, duplicate-email handling.
- Task create/edit/delete for employers, HR assignment dropdown, due dates, priorities, progress, search and status filters.
- HR status/progress updates, blocker reason, task activity audit trail.
- Shared interview list, HR-only scheduling/cancellation, date/time validation, candidate details, duration, related task, meeting link and Join action.
- Overview metrics, upcoming interviews, recent activity, responsive desktop/tablet/mobile layout.

## Requirements
- Python 3.11+
- Node.js 20+ (Node 22 is fine)
- npm

## Run locally (Windows PowerShell)
### 1. Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### 2. Frontend (second terminal)
```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```
Open http://localhost:3000

## First-use workflow
1. Register an **Employer** account.
2. Register a second account and choose **HR**.
3. Sign in as Employer and create a task; select the HR account from the assignment list.
4. Sign in as HR to see assigned tasks and update progress. HR can schedule interviews.
5. Sign in as Employer to see the same interview list and use the Join button.

## Environment variables
Backend `.env`:
```env
JWT_SECRET=replace-with-a-long-random-secret-before-deployment
FRONTEND_ORIGIN=http://localhost:3000
# Optional for a managed database:
# DATABASE_URL=postgresql+psycopg://user:password@host:5432/salarite
```
Frontend `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

The default database file is `salarite_auth.db` so it does not collide with an earlier demo database schema. The database is created on first backend start.

## API routes
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/users` (HR account list)
- `GET/POST /api/tasks`, `GET/PATCH/DELETE /api/tasks/{id}`
- `POST /api/tasks/{id}/status`, `POST /api/tasks/{id}/progress`
- `GET /api/dashboard/summary`, `GET /api/activity`
- `GET/POST /api/interviews`, `POST /api/interviews/{id}/cancel`

## Security and production notes
- Set a strong random `JWT_SECRET` before deployment; never use the development fallback in production.
- JWT is stored in `localStorage` for this assignment MVP. For a production app, prefer secure, HttpOnly, SameSite cookies, rate limiting, email verification, password reset, refresh-token strategy and audit logging.
- This MVP uses SQLite and `create_all`; use Alembic migrations and managed PostgreSQL for production.
- Interview Join buttons open the meeting/call URL supplied by HR. This app does not itself provide video/voice/chat infrastructure.
- Run `npm run lint` to type-check the frontend. Deployment, production security review and end-to-end testing remain separate steps.

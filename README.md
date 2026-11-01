# CampusFix

**Campus care, clearly handled.** A premium, Dockerized campus maintenance and complaint management platform. Students can report issues, follow progress and see updates; administrators can triage requests and monitor service performance.

## Stack
- React 19 + Vite + custom responsive design system
- FastAPI + SQLAlchemy + JWT authentication
- PostgreSQL 16
- Docker Compose + Nginx reverse proxy
- GitHub Actions CI checks

## Run with Docker (recommended)
1. Install Docker Desktop and start it.
2. Copy `.env.example` to `.env` and change `POSTGRES_PASSWORD`, `JWT_SECRET`, and `ADMIN_PASSWORD`.
3. From this directory run:

   ```bash
   docker compose up --build
   ```
4. Open [http://localhost:8080](http://localhost:8080).

The local administrator account is configured through `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`. The example values are for local development only. Change them before exposing the app to any network. Students can register from the sign-in screen.

## API
- `GET /api/health` — health check
- `POST /api/auth/register` — create student account
- `POST /api/auth/login` — get access token
- `GET /api/auth/me` — current account
- `GET /api/users` — list staff/admin accounts (admin only)
- `GET /api/complaints` — list complaints (role-aware)
- `POST /api/complaints` — create complaint
- `PATCH /api/complaints/{id}` — admin update/status/assignment
- `GET /api/dashboard/stats` — dashboard metrics
- `GET /docs` — interactive FastAPI docs on the backend service (port 8000)

## Local development
Backend: create a virtual environment, install `backend/requirements.txt`, set `DATABASE_URL`, then run `uvicorn app.main:app --reload --app-dir backend` from the project root.

Frontend: `cd frontend && npm install && npm run dev` (Vite proxies `/api` to `http://localhost:8000`).

## Current MVP scope
The first implementation includes account registration/login, role-aware complaint visibility, complaint creation, admin status/priority/assignee API updates, live dashboard metrics, request filtering/search, and responsive dashboard screens. File/image attachments, staff invitation/creation UI, email notifications, and production deployment hardening are planned follow-up work rather than being represented as complete.

## Security notes
- Passwords are hashed; JWT secrets and credentials are environment variables.
- Public registration always creates a student. Admin registration is disabled.
- This starter is intended for local development and demonstration. Add HTTPS, rate limiting, backups, email delivery, database migrations, and a managed secrets store before production deployment.

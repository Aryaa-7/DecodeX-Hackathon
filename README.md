# ATMS MVP

FastAPI + MongoDB/PyMongo + OR-Tools backend and React/Vite/TypeScript frontend for academic timetable generation. MongoDB is the persistence store; when MongoDB is unavailable during a local demo, the API uses an explicitly limited in-memory adapter and reports `mongodb:false` at `/health`.

## PowerShell setup

```powershell
Copy-Item .env.example .env
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
# Start MongoDB separately, then:
$env:PYTHONPATH=(Get-Location).Path
uvicorn backend.app.main:app --reload
# In another PowerShell:
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Select seeded Admin, Teacher, or Student profiles. Admin can generate a validated timetable; other profiles see their scoped timetable and notifications. Backend demo identity is selected with `X-User-Id` and is checked server-side.

## Tests and API

```powershell
$env:PYTHONPATH=(Get-Location).Path
pytest -q backend\tests
```

Important endpoints: `POST /generate`, `GET /timetable?view=section|faculty|room&id=...`, `POST /validate-move`, `POST /move`, `POST /undo`, `GET /vacancy/rooms`, `POST /events`, notification CRUD/config/demo-time, and encrypted relay endpoints under `/chat`.

## Data and collections

Academic CSV data is loaded/upserted at startup from `data\timetable_courses.csv` (campus CSVs are supported when supplied). MongoDB collections include users, faculty, rooms, sections, courses, timetables, events, proposals, undo_stack, notifications, notification_config, conflicts, chat_conversations and chat_messages.

The chat API accepts only ciphertext and IV. A production-ready client should use Web Crypto AES-GCM with a key exchanged out-of-band; this MVP intentionally does not claim Signal/MLS security and never logs or persists plaintext.

Troubleshooting: confirm MongoDB is listening at `MONGODB_URI`, run `GET /health`, and use `npm run build` in `frontend` to verify the UI. The fallback is for local demos only and is not durable across restarts.

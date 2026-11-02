# School System — local development

Open `School System.code-workspace` in VS Code. The workspace selects `.venv\Scripts\python.exe` and provides a Django debugger (F5).

## Isolated Python environment

This checkout uses Python 3.12 with packages installed only in `.venv`.
The pre-existing `venv` folder was left untouched; its original Python installation is missing.

Run from this project folder in PowerShell; activation is optional:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

To recreate the environment using an installed Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
```

`requirements.txt` is the original dependency declaration. `requirements.lock.txt` records the versions installed for this setup.

## Services and data

The application is configured for PostgreSQL using the existing private `.env` file. PostgreSQL must be available and the configured database must exist before database-dependent operations will work. Apply migrations when the database is ready:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

Redis is needed if you run the optional Celery background workers. Python client packages do not install PostgreSQL or Redis servers.

## Repository

The local Git repository uses branch `main`. Credentials (`.env`), virtual environments, uploads, logs, and generated files are ignored. The source includes existing demo account credentials in the seed command and documentation; use them only for local sample data.

# Repository Guidelines

## Project Structure & Architecture

`backend/` contains Flask API blueprints in `routes/`, SQLAlchemy entities in `models/`, integration logic in `services/`, helpers in `utils/`, and tests in `tests/`. `frontend/` is a Vue 3/Vite SPA; put pages in `src/views/`, reusable UI in `src/components/`, Pinia state in `src/stores/`, and routing in `src/router/`. Documentation is under `docs/`; deployment helpers and service units are in `scripts/` and `systemd/`. The multi-stage `Dockerfile` builds the SPA and serves it through Flask/Gunicorn.

## Build, Test, and Development Commands

- `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` prepares a desktop backend environment.
- `cd backend && python app.py` starts Flask on port 5000 with mock GPIO behavior for normal local development.
- `cd frontend && npm ci && npm run dev` installs locked dependencies and starts Vite on port 5173; `/api` requests proxy to Flask.
- `cd frontend && npm run build` produces the production SPA in `frontend/dist/`.
- `cd backend && python -m unittest discover -s tests -p 'test_*.py'` runs backend tests.
- `docker compose up --build` builds and runs the complete desktop stack.

## Coding Style & Naming Conventions

Use four-space indentation and `snake_case` for Python functions/modules; use `PascalCase` for classes. Keep route handlers thin and move device or integration behavior into services. In Vue and JavaScript, follow the existing two-space style, use `camelCase` identifiers, and name components in `PascalCase.vue`. No formatter or linter is configured, so match adjacent code and keep diffs focused.

## Testing Guidelines

Tests use Python's `unittest`; name files `test_*.py`, classes `*Test`, and methods `test_*`. Mock schedulers, GPIO, network calls, and time-dependent integrations. Add regression coverage for affected backend behavior. There is no frontend test suite or coverage threshold, so UI changes require a production build plus manual browser checks of affected roles and responsive layouts.

## Commits & Pull Requests

Recent history uses concise imperative subjects such as `Fix calendar scheduler app context`; keep each commit scoped to one change. Pull requests should explain behavior, configuration or migration impact, and validation performed; link relevant issues and include screenshots for UI changes. Call out Raspberry Pi/GPIO or calendar steps that require hardware testing.

## Security & Configuration

Never commit `.env` files, signing keys, ngrok credentials, calendar URLs, database snapshots, or logs. Use mock GPIO locally, and document new operational settings in `docs/` and Compose files.

# Shipyard

Shipyard is a production-style engineering workflow platform for managing projects, issues, release checklists, notifications, and audit history.

## Tech stack

- Frontend: React, TypeScript, Vite
- Backend: Python, Flask, SQLAlchemy
- Database: PostgreSQL
- Local development: Docker Compose
- Planned: GitHub Actions, AWS, Terraform, Redis, OpenTelemetry

## Local setup

### Requirements

- Docker Desktop
- Node.js
- npm

### Start the API and database

```bash
cp .env.example .env
docker compose up --build
```

The API health endpoint is available at:

```text
http://localhost:5000/api/v1/health
```

### Start the frontend

```bash
cd apps/web
cp .env.example .env
npm install
npm run dev
```

Open the local URL shown by Vite, usually `http://localhost:5173`.

## Current phase

Phase 0: Project foundation, Flask health endpoint, React-to-API connectivity, PostgreSQL Docker service.
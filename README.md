# AI Software Planning Engineering Assistant

An AI-native software engineering assistant that transforms a natural-language software idea into a structured, traceable, validated engineering blueprint.

The product is intentionally not a chatbot clone. It is designed as a supervisor-led multi-agent workflow:

User Requirement -> Requirement Analysis -> System Architecture -> Database Design -> API Design -> Implementation Plan -> Documentation -> Validation -> Final Engineering Blueprint

## Milestone 1 Status

This repository currently contains the project foundation:

- React + TypeScript + Tailwind frontend
- FastAPI + Pydantic backend
- MongoDB service through Docker Compose
- Environment-based configuration
- Health-check API
- Initial dashboard and workflow visualization shell
- Agent-oriented backend package structure
- Supervised blueprint workflow endpoint
- Project history with MongoDB-backed persistence and in-memory fallback

## Local Setup

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Start the full stack:

```bash
docker compose up --build
```

3. Open the app:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

## Backend

The backend is organized around clear engineering boundaries:

- `app/api`: HTTP routes
- `app/agents`: specialized agent modules
- `app/core`: settings and application lifecycle
- `app/database`: MongoDB connectivity
- `app/schemas`: Pydantic contracts
- `app/services`: application services
- `app/prompts`: prompt templates kept separate from logic

## Frontend

The frontend starts as an internal engineering platform shell with:

- Project status summary
- Agent execution state
- Workflow stages
- Artifact inspection preview

## Next Milestone

The next milestone should connect the existing structured agent contracts to a Gemini provider implementation and add richer artifact inspection views.

## Persistence

When MongoDB is available, generated blueprints are stored in the `projects` collection. If MongoDB is unavailable during local development, the backend falls back to in-memory session storage so the workflow endpoints still run.

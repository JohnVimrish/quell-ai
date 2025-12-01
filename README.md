# Quell-AI Experience Site

Calm your calls, tame your texts. This repo hosts the interactive marketing experience for the Quell-AI communicator copilot. It highlights how Quell-AI auto-attends calls and texts on your behalf, filters spam, and delivers trustworthy summaries - all while keeping privacy front and center.

---

## Product snapshot

### Key capabilities

- **Unified sessions** - calls, video meetings, and chat threads flow through one decision engine with shared guardrails.
- **Delegation rules** - auto-join Zoom/Teams when you are busy, or hand chat mentions back when a VIP pings you.
- **Instruction feed** - short-lived guidance scoped by channel, meeting title, or contact, with automatic expiry.
- **Document policies** - upload briefs and set who, when, and where the assistant is allowed to share them.
- **Voice cloning controls** - opt-in voice, disclosure toggles, and audit logs before the assistant speaks for you.
- **Mind-map summaries** - meetings and calls distilled into highlights, topics, and action items.
- **Spam and safety** - layered models keep unwanted calls, phishing texts, and unknown meeting invites at bay.
- **Searchable transcripts** - keyword search across calls, meetings, and chat logs in one place.
- **Modular stack** - bring your own telephony, transcription, and TTS providers.

### Why Quell-AI stands apart

| Feature / App                   | Quell-AI | Truecaller / Hiya | Google Call Screen | Business AI Assistants |
|---------------------------------|----------|--------------------|--------------------|------------------------|
| Copilot mode toggle             | Yes      | No                 | No                 | No                     |
| Instruction feed (temp memory)  | Yes      | No                 | No                 | No                     |
| Sensitive info guardrails       | Yes      | No                 | No                 | No                     |
| Mind-map summaries              | Yes      | No (logs only)     | No (transcripts)   | No (notes only)        |
| Voice cloning (transparent)     | Yes      | No                 | No (robotic)       | No (generic)           |
| Whitelist contacts untouched    | Yes      | Yes                | No                 | No                     |
| Keyword spam block (SMS)        | Yes      | No (number only)   | No                 | No                     |
| Time-boxed AI mode              | Yes      | No                 | No                 | No                     |
| Open source + BYOK              | Yes      | No                 | No                 | No                     |
| Policy audit trail              | Yes      | No                 | No                 | Partial                |

---

## What's inside

- **Multi-channel session engine** - unified calls, meetings, and chat via `/api/meetings`, `/api/calls`, and `/api/texts` using the new communication session model.
- **Document policy manager** - configure share rules at `/documents` with `/api/documents` audit trails and retention settings.
- **Settings service** - `/api/settings` exposes voice clone, delegation, and retention toggles surfaced in the SPA.
- **Engaged navigation flow** - a centered landing nav (`About | Engage with the Application | Log in`) that expands into the full product surface when visitors engage or log in, and collapses when they log out.
- **Hover "Back to About" control** - appears while hovering over "Engage with the Application" or when browsing the engaged views (`/why`, dashboard shells, etc.). Clicking it snaps visitors back to the landing layout without a full reload.
- **Why Quell-AI page** - reachable at `/why`, featuring interactive storytelling, the 3D phone demo component, and mock scenarios that highlight contextual intelligence, privacy, and adaptive learning.
- **Message understanding lab** - experiment at `/labs/message-understanding` with a split-view flow that simulates language detection, safer recursive splitting, chunk summaries, and an image captioning stub.
- **Legacy auth stubs** - static login and signup HTML files in `frontend/legacy/` for linking from the SPA while the real auth flow is under construction.
- **Backend scaffolding** - Flask app factory, blueprint registration, asset manifest loader, and graceful shutdown hooks for database and ML services to support the experience frontend.

---

## Repository layout

```
.
├── backend/                 # Flask service (REST blueprints, Socket.IO, asset serving)
│   ├── api/                 # Application logic and blueprints
│   │   ├── app.py           # create_app(), route wiring, SPA shell
│   │   ├── controllers/     # REST endpoints (feed, copilot, auth, etc.)
│   │   ├── db/              # Connection pool manager and helpers
│   │   ├── models/          # Spam detector, RAG system, voice model
│   │   └── utils/           # Config loader, logging helpers, validation
│   ├── app/asset_loader.py  # Vite manifest integration for Flask templates
│   └── static/dist/         # Built frontend assets copied in for production
├── frontend/                # Vite + React SPA (experience shell)
│   ├── src/
│   │   ├── App.tsx          # Routes, lazy-loaded pages, layout wrapper
│   │   ├── components/      # NavBar, AuthProvider, Phone3D, etc.
│   │   ├── pages/           # Landing, WhyQuellAI, dashboard shells, auth
│   │   └── styles/theme.css # Global design tokens and component styling
│   ├── legacy/              # Static login/signup HTML views
│   ├── public/              # Static assets served via Flask `/assets/*`
│   └── dist/                # Frontend build output (gitignored, copied to backend)
├── node_build.txt           # Reference build script (Docker exec + copy dist)
└── documents/, extras/, logs/, etc.
```

---

## Tech stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Frontend     | React 19, Vite 7, TypeScript 5.8, CSS-in-files (theme.css) |
| Backend      | Flask, Flask-SocketIO, psycopg2 pool                    |
| Realtime UX  | Custom state machine inside `AuthProvider` + `NavBar`   |
| ML scaffolds | Spam detector, RAG system, voice model placeholders     |
| Tooling      | Docker (optional), npm, Python virtualenv               |

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+ (or use the provided Docker setup)
- Docker Desktop (optional, recommended for uniform Node builds)

### Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # PowerShell on Windows
pip install -r extras/requirements.txt
cp .env.example .env            # configure DATABASE_URL, provider keys, etc.
```

Start the API in development mode:

```bash
flask --app api.app:create_app --debug run
```

### Conversation Lab ingestion worker

File uploads in the Conversation Lab now enqueue background jobs that perform parsing, analytics, and embedding generation. Run a Celery worker next to the Flask API (Redis is the default broker/result backend):

```bash
celery -A worker.celery_app worker -l info
```

Configure `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` if you are not using `redis://localhost:6379/0`. Uploaded payloads are staged under `CONVERSATION_LAB_UPLOAD_DIR` (defaults to `backend/uploads/conversation_lab`) until the worker finishes processing them.

You can throttle concurrent ingest jobs per session by setting `LAB_MAX_PENDING_UPLOADS` (default `5`). When the queue is full, `/api/labs/conversation/ingest` responds with HTTP 202 and a `Retry-After` header so the frontend can pause before retrying.

For real-time status updates from background workers, set `SOCKETIO_MESSAGE_QUEUE` (defaults to the Celery broker URL). The Flask app and Celery workers will publish ingest events over that Redis channel, and the frontend subscribes via Socket.IO. If the message queue isn’t configured, the UI falls back to polling.

### Embedding queue

Both the API and ingestion worker reuse a shared embedding queue so Ollama stays warm between requests. Tune the number of background embedding threads by setting `EMBED_QUEUE_WORKERS` (default `2`). The queue also caches recent embeddings for a short period to avoid recomputing unchanged content.

### Session cache priming

To keep file uploads fast, `prime_session_cache` is debounced within the worker. Use `PRIME_SESSION_DEBOUNCE` (seconds, default `60`) to control how often each session/user combination is primed.

### Frontend retry cache

Conversation Lab caches the last few uploaded files (up to `MAX_CACHED_FILES` in code) in memory, keyed by their SHA-256 hash. When an ingest job fails, the UI presents a “Retry upload” button that reuses the cached file so the user doesn’t have to reselect it. The cached entry is released once the upload reaches the `ready` state.

If the primary Ollama embedding model is unavailable, workers automatically fall back to `sentence-transformers/all-MiniLM-L6-v2`. Override this by setting `FALLBACK_EMBED_MODEL` to any SentenceTransformers checkpoint.

The app factory auto-loads configuration, sets up CORS, registers all blueprints, and serves the SPA shell for non-API routes. Graceful shutdown now closes pooled database connections and calls ML model `cleanup()` hooks.

### Frontend setup

Install dependencies directly:

```bash
cd frontend
npm install
npm run dev
```

Or use the project's container workflow (mirrors `node_build.txt`):

```bash
docker compose -f extras/node.yml up -d                # start node-frontend container
docker exec -it node-frontend npm install              # install packages inside container
docker exec -it node-frontend npm run dev              # Vite dev server on http://localhost:5173
```

The SPA proxies `/api/*` calls to `http://127.0.0.1:5000` while in development.

---

## Building for production

From the host (or CI) use the provided script as reference:

```bash
# Build inside the container
docker exec node-frontend npm run build

# Copy artifacts into the Flask static directory
xcopy /E /I /Y frontend\dist backend\static\dist
```

The Flask app serves assets from `backend/static/dist` and resolves hashed filenames via `asset_loader.py`. Ensure the build step runs before deploying the backend so `static/dist/.vite/manifest.json` exists.

---

### Labs pipeline configuration

To swap the lab demo over from deterministic stubs to real detection/translation/embedding services, set the provider and credentials via environment variables:

```bash
# Required when using OpenAI
export LABS_PIPELINE_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Optional overrides
export LABS_OPENAI_MODEL=gpt-4o-mini
export LABS_OPENAI_TRANSLATE_MODEL=gpt-4o-mini
export LABS_OPENAI_EMBED_MODEL=text-embedding-3-small
export LABS_OPENAI_EMBED_DIM=1536
```

If `LABS_PIPELINE_PROVIDER` is not set (or the API call fails), the pipeline falls back to the deterministic heuristics so the UI keeps working offline.

### Database setup for labs features

The labs experience stores messages, chunks, and image captions in Postgres with pgvector. Run the helper schema once (requires the `vector` extension):

```bash
psql "$DATABASE_URL" -f backend/api/db/migrations/labs_schema.sql
```

The Flask controller also runs the same statements on startup as a safety net, but applying the SQL yourself avoids repeated DDL checks in production.

---

## Navigation behaviour at a glance

| State                      | Visible nav                               | Notes                                                         |
|----------------------------|-------------------------------------------|---------------------------------------------------------------|
| Default visitor            | `About | Engage with the Application | Log in` | Centered pills; hover over Engage reveals "Back to About".    |
| Engaged (clicked Engage)   | `About | Why Quell-AI | Dashboard | Calls | Contacts | Texts | Reports` | Smooth transition, Back button stays available.                |
| Authenticated (login/signup) | `Dashboard | Calls | Contacts | Texts | Reports | Settings | Log out` | Log out returns to landing nav and clears highlights.          |
| Hover / focus on Engage    | Adds `Back to About` control left of the brand | Clicking snaps to `/` without reloading or altering history. |

The experience state is tracked by `AuthProvider.tsx` (`isAuthed`, `isEngaged`), persisted to `localStorage`, and initialised based on the current route. Legacy auth links (`/legacy/login.html`, `/legacy/signup.html`) remain accessible from the header.

---

## Testing & linting

While end-to-end automation is still in flight, you can run available checks with:

```bash
# Type checks and linting
cd frontend
npm run build            # includes `tsc --noEmit`
npm run lint

# Backend tests
cd backend
pytest
```

Additions should maintain ASCII-only source unless there's a clear reason to include Unicode (e.g., localisation assets).

---

## Contributing

1. Fork / branch from `main`.
2. Keep navigation and engagement behaviour consistent with the acceptance criteria above.
3. Run the TypeScript build and relevant backend tests before opening a PR.
4. Update `node_build.txt` and this README if the build pipeline changes.

Design system, copy, or interaction updates live primarily in `frontend/src/styles/theme.css`, `frontend/src/components/NavBar.tsx`, and `frontend/src/components/AuthProvider.tsx`. Backend API additions should follow the existing blueprint pattern under `backend/api/controllers/` and reuse the `DatabaseManager` pool.

---

## License

Apache-2.0 - see [LICENSE](LICENSE) for details.







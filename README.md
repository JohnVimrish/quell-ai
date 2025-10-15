# Quell-AI Experience Site

Calm your calls, tame your texts. This repo hosts the interactive marketing experience for the Quell-AI communicator copilot. It highlights how Quell-AI auto-attends calls and texts on your behalf, filters spam, and delivers trustworthy summaries - all while keeping privacy front and center.

---

## Product snapshot

### Key capabilities

- **Copilot Mode** – smarter than silent mode; toggle AI on/off or set a duration.
- **Instruction Feed** – short-lived tasks the AI can reference (auto-clears in a week).
- **Whitelist Contacts** – important callers bypass the AI entirely.
- **Spam Filtering** – layered number reputation plus keyword heuristics.
- **Mind-Map Summaries** – conversations distilled into actionable highlights.
- **Voice Cloning (opt-in)** – speaks in your voice with transparent disclosure.
- **Searchable Transcripts** – locate keywords across calls and texts.
- **Weekly Reports** – track time saved, spam blocked, and AI-handled volume.
- **Open and modular** – bring-your-own STT, TTS, and telephony providers.

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

=======
# quell-ai
Personal Communicator-Copilot: An AI assistant for calls and texts.


# 📱 Quell AI  
**Calm your calls, tame your texts.**  
An open-source, privacy-first AI copilot that auto-attends calls and texts on your behalf, filters spam, and summarizes conversations you can actually trust.

---

## 🌟 Features
- **Copilot Mode** — like silent/vibrate mode, but smarter. Toggle AI ON/OFF or set it for a duration (e.g., 1 hour).  
- **Instruction Feed** — short-lived tasks the AI can use, auto-cleared after a week (privacy by design).  
- **Whitelist Contacts** — important calls/texts bypass AI entirely.  
- **Spam Filtering** — block spammers using number reputation + keyword filters.  
- **Mind-Map Summaries** — conversations distilled into key-point visuals/snippets.  
- **Voice Cloning (opt-in)** — Quell AI speaks in your voice but always discloses itself.  
- **Searchable Transcripts** — find keywords across calls and texts.  
- **Weekly Reports** — overview of AI-handled calls, spam blocked, time saved.  
- **Open-Source & Modular** — bring-your-own-provider keys (STT, TTS, telephony).  

---

## 🆚 Why Quell AI is Different
| Feature / App | **Quell AI** | Truecaller/Hiya | Google Call Screen | Business AI Assistants |
|---------------|--------------|-----------------|--------------------|------------------------|
| Copilot Mode toggle | ✅ | ❌ | ❌ | ❌ |
| Instruction Feed (temp memory) | ✅ | ❌ | ❌ | ❌ |
| Sensitive info guardrails | ✅ | ❌ | ❌ | ❌ |
| Mind-map summaries | ✅ | ❌ Logs only | ❌ Transcript only | ❌ Notes only |
| Voice cloning (transparent) | ✅ | ❌ | ❌ Robotic | ❌ Generic |
| Whitelist contacts (untouched) | ✅ | ✅ | ❌ | ❌ |
| Keyword spam block (SMS) | ✅ | ❌ Number-only | ❌ | ❌ |
| Time-boxed AI mode | ✅ | ❌ | ❌ | ❌ |
| Open Source + BYOK | ✅ | ❌ | ❌ | ❌ |
| Policy audit (why AI said this) | ✅ | ❌ | ❌ | ⚠️ Partial |

---
**Project Structure**

# 📂 Quell AI – Project Structure

```plaintext
<<<<<<< HEAD
quell-ai/
├─ api/
│  ├─ app.py                      # Flask factory (create_app)
│  ├─ controllers/
│  │  ├─ copilot_controller.py
│  │  ├─ feed_controller.py
│  │  ├─ contacts_controller.py
│  │  ├─ calls_controller.py
│  │  ├─ texts_controller.py
│  │  ├─ report_controller.py
│  │  └─ webhooks_controller.py
│  ├─ repositories/
│  │  ├─ base.py
│  │  └─ feed_repo.py
│  ├─ utils/
│  │  ├─ config.py
│  │  └─ validation.py
│  ├─ db/
│  │  └─ connection.py
│  └─ templates/
│     ├─ base.html
│     ├─ dashboard.html
│     └─ feed.html
├─ config/
│  ├─ queries.json
│  ├─ policies.json
│  └─ providers.json
├─ public/
│  └─ styles.css
├─ tests/
├─ requirements.txt
├─ .env.example
└─ README.md
=======
code/
	api/
		app.py
		run.py
		controllers/
			auth_controller.py
			calls_controller.py
			contacts_controller.py
			copilot_controller.py
			feed_controller.py
			report_controller.py
			texts_controller.py
			webhooks_controller.py
			__init__.py
		db/
			connection.py
			migrations/
			__init__.py
		models/
			rag_system.py
			spam_detector.py
			vector-store.py
			__init__.py
		repositories/
			base.py
			feed_repo.py
			users_repo.py
			__init__.py
		templates/
			base.html
			dashboard.html
			feed.html
		utils/
			config.py
			logging.py
			validation.py
	config/
		app.json
		policies.json
		providers.json
		queries.json
	extras/
		docker-compose.yml
		Dockerfile.api
		requirements.txt
	functionalities/
		ai_instruction.py
		analytics.py
		call.py
		text_message.py
		user.py
		voice_model.py
		__init__.py
	public/
		index.html
		styles.css
	tests/
		test_feed.py
>>>>>>> 5b1bea6 (Initial commit: add all project files)
```

# Quell AI

Personal Communicator-Copilot: An AI assistant for calls and texts.

## Project Layout

```
quell-ai/
├─ backend/          # Flask application (APIs, Socket.IO, database models)
│  ├─ api/
│  ├─ app/
│  ├─ static/        # Production frontend build lives here (dist/)
│  └─ templates/     # Jinja base shell which loads the Vite bundle
├─ frontend/         # Vite + React SPA (JS/TS, CSS, assets)
│  ├─ src/
│  ├─ public/
│  └─ dist/          # Generated build output (gitignored)
├─ extras/           # Docker compose files, helper scripts
└─ documents/, reference_images/, ...
```

## Prerequisites

- Python 3.11+
- Node 18+
- Docker (for optional dev containers)

## Local Development

1. **Backend environment**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows PowerShell
   pip install -r extras/requirements.txt
   cp .env.example .env      # ensure DATABASE_URL etc.
   ```

2. **Frontend dependencies** (packages install inside the `node-frontend` container)
   ```bash
   docker compose -f extras/node.yml up -d
   docker exec -it node-frontend bash -lc "cd /app && npm install"
   ```

3. **Run dev servers**
   - Flask API: `flask --app api.app:create_app --debug run`
   - Vite dev (already running in container): `docker logs -f node-frontend`

   The React app proxies `/api` calls to `http://127.0.0.1:5000`. Visit http://localhost:5173.

## Production Build

```bash
# Frontend
docker exec node-frontend bash -lc "cd /app && npm run build"
cp -r frontend/dist backend/static/dist

# Backend (e.g. gunicorn)
cd backend
pip install -r extras/requirements.txt
FLASK_ENV=production gunicorn "api.app:create_app()"
```

## Docker Image

A multi-stage Dockerfile (node build -> copy dist -> install Python deps) is planned. For now, run the commands above in CI or locally before building any images.

## Tests

- Python: `cd backend && pytest`
- Frontend: `docker exec node-frontend bash -lc "cd /app && npm test"` (configure playwright/cypress as needed).

## Asset Manifest Integration

Flask consumes `backend/static/dist/.vite/manifest.json` via `backend/app/asset_loader.py`. Ensure the manifest exists before running in production (`npm run build`).

🔐 Privacy by Design

1.Feed items auto-delete after 7 days (archive +7 days, then purge).
2.Sensitive input (bank, SSN, etc.) flagged before saving.
3.Whitelisted contacts = never intercepted by AI.
4.Recordings/transcripts are opt-in only.
5.AI always discloses itself on calls.

🧩 Roadmap



📜 License

Apache-2.0 (see LICENSE)

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
quell-ai/
│ │ └─ reputation/
│ │ └─ truecaller_adapter.py
│ ├─ repositories/
│ │ ├─ base.py
│ │ ├─ calls_repo.py
│ │ ├─ texts_repo.py
│ │ ├─ feed_repo.py
│ │ ├─ contacts_repo.py
│ │ └─ embeddings_repo.py
│ ├─ domain/
│ │ ├─ models.py # dataclasses: Call, TextMessage, FeedItem, Contact…
│ │ └─ value_objects.py # PhoneNumber, Duration, UserId…
│ ├─ db/
│ │ ├─ connection.py # SQLAlchemy/psycopg pool + session
│ │ └─ migrations/ # SQL migrations
│ ├─ utils/
│ │ ├─ config.py # loads .env + config/*.json
│ │ ├─ validation.py # sensitive data guards, schema checks
│ │ ├─ auth.py # login/session helpers
│ │ ├─ clock.py # testable time source
│ │ └─ logging.py
│ └─ templates/ # Jinja2 HTML + minimal CSS
│ ├─ base.html
│ ├─ dashboard.html
│ ├─ feed.html
│ ├─ contacts.html
│ ├─ transcripts.html
│ ├─ texts.html
│ ├─ report.html
│ └─ voice.html
├─ config/
│ ├─ queries.json # named SQL/DSL (no inline SQL in code)
│ ├─ policies.json # disclosure text, default rules, spam keywords
│ ├─ providers.json # which adapters active (dev vs prod)
│ └─ env/
│ ├─ dev.json
│ ├─ stage.json
│ └─ prod.json
├─ public/ # static assets (css/js/img)
├─ tests/
├─ .env.example
├─ requirements.txt
└─ README.md

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
```


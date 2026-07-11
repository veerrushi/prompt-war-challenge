# 🌧️ RainReady AI — Monsoon Preparedness & Citizen Assistance

> A production-ready GenAI web application built for the **Google PromptWars Hackathon**.  
> RainReady AI is an empathetic conversational assistant that helps individuals, families,
> and communities prepare for, survive, and recover from monsoon season.

---

## 📌 Chosen Vertical

**Monsoon Preparedness & Citizen Assistance**

India and other South Asian nations experience monsoons that affect hundreds of millions of people annually. Yet most citizens lack personalised, real-time guidance on how to prepare. RainReady AI fills that gap by providing:

- 🧳 Tailored emergency packing checklists
- 🗺️ Location-aware travel and evacuation advisories
- 🏠 Home-safety and flood-proofing tips
- 🚨 Triage guidance before professional help arrives
- ✅ Before / During / After storm action plans

---

## 🧠 Approach & Logic

### 1. Domain-Constrained LLM

The assistant is grounded via a **carefully engineered system prompt** injected at the start of every conversation. The prompt:

- Assigns the AI a clear persona ("Monsoon Preparedness AI")
- Lists concrete responsibilities (checklists, advisories, safety tips)
- Enforces guardrails — off-topic questions are politely declined
- Instructs the model to ask clarifying questions (e.g., location, family size) when context is missing
- Mandates Markdown-formatted, concise, actionable responses

### 2. Streaming Architecture

Tokens are streamed from the Groq API over SSE (Server-Sent Events) and rendered on the frontend progressively. This delivers a fast perceived response time — the user sees the first token in under a second even for long answers.

```
Browser  ──POST /api/chat──►  FastAPI  ──stream──►  Groq (LLaMA 3.3-70B)
         ◄── SSE tokens ──────────────────────────────────────────────────
```

### 3. Rate Limiting & Validation

| Layer | Mechanism |
|---|---|
| Input validation | Pydantic v2 with `Literal` role constraint and `min_length` |
| Rate limiting | SlowAPI – 20 requests/minute per IP |
| Error handling | Groq `APIError` caught separately from generic exceptions |

### 4. Stateless Backend

Conversation history is managed **entirely on the client**. Each request carries the full message list, so the backend remains stateless and horizontally scalable with zero session affinity requirements.

---

## 🗂️ Project Structure

```
prompt-war-challenge/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, routers
│   ├── api/
│   │   └── chat.py          # POST /api/chat endpoint (SSE streaming)
│   ├── core/
│   │   ├── config.py        # Pydantic-settings configuration
│   │   └── limiter.py       # SlowAPI rate-limiter singleton
│   ├── models/
│   │   └── schemas.py       # ChatRequest / Message Pydantic models
│   └── services/
│       └── groq_service.py  # AsyncGroq client wrapper & streaming logic
├── static/
│   ├── index.html           # Single-page UI
│   ├── app.js               # Fetch-based SSE client, Markdown rendering
│   └── styles.css           # UI styles
├── tests/
│   ├── conftest.py          # Shared pytest fixtures (TestClient)
│   ├── test_api.py          # Route & validation integration tests
│   └── test_groq_service.py # GroqService unit tests (fully mocked)
├── Dockerfile               # Multi-stage Docker build
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## ⚙️ How the Solution Works

1. **User types a message** in the browser chat interface.
2. The frontend **appends the message to local history** and sends the full conversation list to `POST /api/chat`.
3. FastAPI validates the payload (Pydantic) and checks the rate limit (SlowAPI).
4. `GroqService.generate_chat_stream()` **prepends the system prompt** and opens an async streaming call to the Groq API (LLaMA 3.3-70B Versatile).
5. Tokens are **yielded as an `AsyncGenerator`** and returned as a `StreamingResponse` with `media_type="text/event-stream"`.
6. The browser's `ReadableStream` reader **renders tokens in real-time** using `marked.js` for Markdown formatting.
7. Once the stream closes, the final assistant message is appended to local history for context on the next turn.

---

## 🚀 Running Locally

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com/)

### Steps

```bash
# 1. Clone the repo
git clone <repo-url>
cd prompt-war-challenge

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and set:  GROQ_API_KEY=your_key_here

# 5. Start the development server
uvicorn app.main:app --reload --port 8080
```

Open **http://localhost:8080** in your browser.

Interactive API docs are available at **http://localhost:8080/docs**.

---

## 🧪 Running Tests

Tests mock the Groq API — no real tokens are consumed.

```bash
pytest tests/ -v
```

| Test file | Coverage |
|---|---|
| `test_api.py` | Root route, health check, validation (empty messages, invalid role), rate limiting |
| `test_groq_service.py` | Token streaming, system-prompt injection, APIError handling |

---

## 🐳 Docker

```bash
# Build
docker build -t rainready-ai .

# Run
docker run -p 8080:8080 -e GROQ_API_KEY=your_key_here rainready-ai
```

---

## ☁️ Deployment to GCP Cloud Run

```bash
gcloud run deploy rainready-ai \
  --source . \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY="your_key_here"
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn, SlowAPI |
| **LLM** | Groq API — LLaMA 3.3-70B Versatile |
| **Validation** | Pydantic v2 (`pydantic-settings`) |
| **Frontend** | Vanilla HTML / CSS / JavaScript, marked.js |
| **Testing** | pytest, pytest-asyncio, httpx |
| **Deployment** | Docker, Google Cloud Run |

---

## 📋 Assumptions Made

| Assumption | Rationale |
|---|---|
| Client-side conversation history is sufficient | Keeps the backend stateless and scalable; a real product might add a session store. |
| `marked.js` loaded from CDN | Acceptable for a hackathon prototype; a production build would bundle it. |
| Modern browsers with Fetch API streaming support | All evergreen browsers support `ReadableStream`; legacy support was out of scope. |
| A single Groq API key is shared across all users | Rate-limiting (20 req/min/IP) mitigates abuse; a production system would use per-user keys or quotas. |
| `llama-3.3-70b-versatile` is available on the Groq free tier | Confirmed at time of development; the model name is extracted into a constant for easy swapping. |

---

## 📝 License

MIT

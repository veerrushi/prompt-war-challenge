# RainReady AI - Monsoon Preparedness & Citizen Assistance

A lightweight, production-ready GenAI web application built for the Google PromptWars hackathon. This application serves as a smart assistant to help individuals and communities prepare for the monsoon season.

## Chosen Vertical & Approach
**Vertical:** Monsoon Preparedness & Citizen Assistance

**Approach:**
We designed a conversational AI assistant tailored specifically to handle monsoon-related inquiries. 
- **Context-Aware:** The assistant asks for location and family context if not provided, allowing it to generate highly personalized checklists, travel advisories, and safety recommendations.
- **Guardrails:** The system prompt restricts the AI from answering non-emergency, off-topic questions.
- **Fast & Efficient:** Uses Groq's high-speed inference API with Llama-3.3-70b-versatile, streaming tokens directly to the frontend for a responsive user experience.
- **Secure & Production Ready:** Includes IP-based rate limiting (`slowapi`), Pydantic validation, environment variables for secrets, and Dockerization for easy deployment on GCP Cloud Run.

## Tech Stack
- **Backend:** Python, FastAPI, Uvicorn, SlowAPI
- **LLM:** Groq API (Llama-3.3-70b-versatile)
- **Frontend:** Vanilla JS, HTML, CSS (marked.js for Markdown rendering)
- **Deployment:** Docker, Google Cloud Run

## How to Run Locally

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Copy `.env.example` to `.env` and add your Groq API key.
   ```bash
   cp .env.example .env
   # Edit .env and set GROQ_API_KEY
   ```

3. **Run the Server:**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```
   Open `http://localhost:8080` in your browser.

## Running Tests
Tests use `pytest` and mock the Groq API so no real tokens are consumed during testing.
```bash
pytest tests/
```

## Deployment to GCP Cloud Run

The app is containerized and reads the `PORT` environment variable.

1. **Build and Deploy:**
   ```bash
   gcloud run deploy monsoon-ai \
     --source . \
     --port 8080 \
     --allow-unauthenticated \
     --set-env-vars GROQ_API_KEY="your_api_key_here"
   ```

## Assumptions Made
- Users have modern browsers capable of Fetch API streaming.
- Client-side history management is sufficient for this scope (stateless backend).
- The `marked.js` library is loaded via CDN.

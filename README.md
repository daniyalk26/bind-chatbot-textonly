# Bind IQ – Text-Only On-Boarding Chatbot

A full-stack web chatbot that walks users through an insurance-style onboarding flow entirely via text.

---

## 🛠️ Tech Stack

| Layer | Tech |
| :--- | :--- |
| **Front-end** | React 18 + TypeScript + Vite + Tailwind |
| **Back-end** | FastAPI • SQLModel • Uvicorn |
| **AI Services** | OpenAI Chat + Whisper + TTS APIs |
| **Database** | PostgreSQL 15 |
| **Container** | Docker & Docker Compose |

---

## 📂 Repository Layout

.
├── backend/            # FastAPI application
│   ├── main.py         # WebSocket endpoint & routing logic
│   ├── models.py       # SQLModel ORM models
│   ├── crud.py         # Database CRUD helpers
│   ├── conversation_* # Finite-state machine prompts & logic
│   ├── openai_client.py# Async wrapper around OpenAI APIs
│   └── requirements.txt
├── frontend/           # React (Vite) single-page app
│   └── src/…           # Components, api.ts WebSocket wrapper, etc.
├── docker-compose.yml  # 3-service stack: postgres | backend | frontend
└── Dockerfile(s)       # Separate images for back- and front-end


---

## 🚀 Quick-start with Docker

> **Prerequisite:** Docker ≥ 23 & Docker Compose plugin.

1.  **Clone & enter the repo**
    ```bash
    git clone [https://github.com/daniyalk26/bind-chatbot-textonly.git](https://github.com/daniyalk26/bind-chatbot-textonly.git)
    cd bind-chatbot-textonly
    ```

2.  **Add secrets** (creates `backend/.env`) (add env in backend folder)
    ```bash
    # Create the environment file from the example
    cp backend/.env.example backend/.env
    ```
    Now, open `backend/.env` and add your OpenAI API key and database url
    ```ini
    OPENAI_API_KEY=<your-key>
    DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/bindiq_db

    ```

3.  **Spin up the full stack**
    ```bash
    docker compose up --build
    ```
    Compose spins up these services. You can access them on the following ports:

| Service | Purpose | Exposed Port |
| :--- | :--- | :--- |

| `backend` | FastAPI + WebSocket | `8000` |
| `frontend` | React dev server | `5173` |

Open **http://localhost:5173** in your browser to start chatting.

---




⚙️ Environment Variables
Variable	Location	Description
OPENAI_API_KEY	backend/.env	Required. Your OpenAI secret key.
DATABASE_URL	Compose inline	


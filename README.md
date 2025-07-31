# Bind IQ – Text-Only On-Boarding Chatbot

A full-stack web chatbot that walks users through an insurance-style onboarding flow entirely via text.

---

## ✨ Features

- **Text-Only Interaction**: A streamlined and reliable text-based conversation for user onboarding.
- **AI-Powered Conversation**: Uses OpenAI language models to understand and generate natural user interactions.
- **Data Persistence**: Uses a PostgreSQL database to store user information and conversation history.
- **Containerized Deployment**: Comes with pre-configured Docker and Docker Compose files for a simple, one-command setup.
- **Modern Tech Stack**: Built with FastAPI for the backend and React with TypeScript for the frontend.

---

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI** for high-performance REST and WebSocket endpoints.
- **SQLModel** for ORM and data validation, combining SQLAlchemy and Pydantic.
- **Uvicorn** as the ASGI server.
- **OpenAI API** for natural language generation.

### Frontend (React + TypeScript)
- **React 18** with **TypeScript** for a type-safe, component-based UI.
- **Vite** as the build tool for a fast development experience.
- **Tailwind CSS** for utility-first styling.

---

## 📋 Prerequisites

- Docker & Docker Compose
- An **OpenAI API key**
- (**Optional**) A PostgreSQL client like DataGrip to inspect the database.

---

## 🚀 Installation & Setup

### Using Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/daniyalk26/bind-chatbot-textonly.git](https://github.com/daniyalk26/bind-chatbot-textonly.git)
    cd bind-chatbot-textonly
    ```

2.  **Create the environment file**:
    Create a `.env` file in the `backend` directory by copying the example file.
    ```bash
    cp backend/.env.example backend/.env
    ```
    Now, add your API key to the `backend/.env` file:
    ```env
    # .env in the 'backend' directory

    # API Keys
    OPENAI_API_KEY=your_openai_api_key_here

    # Database URL for Docker Compose
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/bindiq_db
    ```

3.  **Start the application**:
    ```bash
    docker compose up --build
    ```
    This will start:
    - Backend API on `http://localhost:8000`
    - Frontend on `http://localhost:5173`
    - PostgreSQL database (internal to Docker)

---

## 🎮 Usage

1.  Open your browser and navigate to **`http://localhost:5173`**.
2.  The chat interface will appear, and you can begin typing to start the onboarding process.

### Conversation Flow
The chatbot will guide you through collecting key information for an insurance quote, such as:
1.  Full name and email
2.  ZIP code
3.  Vehicle information (year, make, model)
4.  Other relevant details for the quote

### Connecting to the Database with DataGrip
To view the database tables created by the application:
1.  Expose the PostgreSQL port by adding a `ports` section to the `postgres` service in your `docker-compose.yml` file:
    ```yaml
    services:
      postgres:
        # ... other settings
        ports:
          - "5432:5432" # Expose port 5432 to the host
    ```
2.  Restart your containers: `docker compose up -d`.
3.  In DataGrip, establish a new PostgreSQL connection with the following credentials:
    - **Host**: `localhost`
    - **Port**: `5432`
    - **User**: `postgres`
    - **Password**: `postgres`
    - **Database**: `bindiq_db`

---


# Visual Semantic Search

# Application Architecture
<img width="1603" height="954" alt="app_arch" src="https://github.com/user-attachments/assets/cc45a0cd-8662-4dcd-ade8-6ef0ce4c2cc1" />

# Cloud Architecture
<img width="2315" height="954" alt="cloud" src="https://github.com/user-attachments/assets/e2b4b77e-889a-4325-8f96-fa378ce7ea38" />

# UI
![alt text](image.png)


---
## Overview

Visual Semantic Search is a full-stack AI application enabling semantic image search using OpenAI's CLIP model and FAISS vector indexing. It comprises:

- **Backend:** FastAPI server serving REST API endpoints, FAISS-based vector search, and static image files.
- **Frontend:** React app (Vite + shadcn/ui) providing an intuitive UI for search and result visualization.
- **Data:** Image assets, embeddings, metadata, and FAISS indices stored on disk.
- **Notebooks:** Jupyter notebooks for data prep, captioning, embedding creation, and index building.
- **Containerization:** Dockerfiles for backend and frontend, orchestrated with Docker Compose for local containerized dev/testing.
---
## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Optional GPU with appropriate CUDA for accelerated inference

### Install Dependencies Locally
Backend (optional outside Docker)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Frontend (optional outside Docker)
cd UI
npm install
npm run dev

---

## Running Locally with Docker Compose

### Build and Start Containers
docker-compose up --build

This will:

- Build the backend container from `Dockerfile.api`
- Build the React frontend container from `UI/Dockerfile`
- Expose Backend API at http://localhost:8000
- Expose Frontend React app at http://localhost:8080 (or 5173 based on your config)

---

## API Endpoints

- **GET /health:** Check system status and model info
- **POST /search:** Submit search query, parameters and receive ranked image results
- **POST /admin/reload:** Reload index and models without restarting server

---

### Backend 

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

---

### Frontend

CMD ["npm", "run", "dev", "--", "--host"]

---

## Notes

- The backend container installs OpenAI’s CLIP repo directly from GitHub; `git` must be installed inside the container.
- React frontend picks up backend URL from environment variable (`VITE_API_BASE_URL`), which points to Docker Compose service name `backend`.
- Use `docker-compose down` to stop containers and `docker-compose logs -f` to tail logs.
- Adjust ports in Dockerfiles and Compose as necessary.

---

## License

MIT License





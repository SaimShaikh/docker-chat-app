# ChatApp (Flask + Socket.IO + MySQL + Nginx, Dockerized)

A minimal real-time chat backend (Flask + Flask-SocketIO) with MySQL storage and Nginx reverse proxy. Tested on Ubuntu 24.04 on EC2 with Docker + docker-compose v2.40.0. 👇 See “What I ran” for the exact terminal steps and gotchas I hit. 

## Tech
- **Backend:** Flask + Flask-SocketIO (eventlet)
- **DB:** MySQL 8.0 (init script creates `messages` table)
- **Proxy:** Nginx → `backend:5000`
- **Orchestrator:** docker-compose (v2.x CLI)
- **Port:** `38080` on host → Nginx `80` → Flask `5000` (matches my EC2 session).
- **Docke and Docker Composer**



---
## How to Run This project
```bash
sudo apt-get update -y
sudo apt-get install docker.io -y
sudo usermod -ag docker $USER
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
docker compose version 
git clone <repo url>
cd <project folder name>
```

* To run Docker Project use this 
``docker-compose up -d --build``
* To Stop Docker Project use this
``docker-compose down ``

---

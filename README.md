# 💬 Docker Chat App  
**Developed & Modified by _Eng. Muhammad Abdulghaffar_**

> Real-time chat app powered by **Flask**, **Socket.IO**, **MySQL**, and **Nginx** — fully containerized using **Docker Compose**.

![Login Screen](docs/login.png)
![Chat Example](docs/chat1.png)
![Chat Multiple Users](docs/chat2.png)

---

## ✨ Features
- 🔐 Secure login with username & password (default: `123`)
- 💬 Real-time bi-directional chat using Socket.IO  
- 🗄️ Persistent storage via MySQL + Docker volume  
- 🌐 Reverse proxy handled by Nginx (WebSocket ready)
- 🎨 Responsive UI using Bootstrap + custom blue gradient theme  
- 🐳 One-command local deployment via Docker Compose

---

## 🧰 Tech Stack
| Layer | Technology |
|-------|-------------|
| Backend | Flask + Flask-SocketIO |
| Database | MySQL 8 (volume `dbdata`) |
| Proxy | Nginx |
| Frontend | HTML + Bootstrap |
| Containerization | Docker & Docker Compose |

---

## 🗂️ Project Structure
├── app.py # Flask + SocketIO backend logic
├── requirements.txt # Python dependencies
├── Dockerfile # Backend image build
├── docker-compose.yml # Orchestrates backend + DB + Nginx
├── nginx.conf # Reverse proxy config
├── db-init/
│ ├── 001_seed.sql
│ └── 002_add_passwords.sql
└── templates/
└── index.html # Responsive Bootstrap UI


---

## 🚀 Run Locally

> Requirements: Docker & Docker Compose

```bash
docker compose up --build
Then open:
👉 http://localhost:38080

🔐 Default Credentials
Username	Password
ahmed	123
mona	123
omar	123

The app auto-creates and hashes passwords if the table or column is missing.

🧱 Architecture
mermaid
Copy code
graph LR
A[Browser UI] --> B[Nginx Reverse Proxy]
B --> C[Flask + Socket.IO Backend]
C --> D[(MySQL Database + Volume dbdata)]
Nginx proxies all traffic and upgrades WebSocket connections

Flask handles events & DB transactions

MySQL persists users and chat history

🐳 Docker Commands
# Start all containers
docker compose up --build

# View running containers
docker compose ps

# Follow logs
docker logs -f chat-backend

# Inspect DB
docker exec -it chat-mysql mysql -uroot -prootpass -e "SELECT * FROM chatdb.messages LIMIT 10;"

# Stop and remove containers + volumes
docker compose down -v

🧪 Troubleshooting

502 from Nginx → backend down → check docker logs -f chat-backend

MySQL column missing → app auto-adds it

Socket not working → ensure browser upgrades to WebSocket (101 Switching Protocols)

🖼️ Screenshots
Login Page

Active Chat

Two Users in Real Time

👨‍💻 Author

Eng. Muhammad Abdulghaffar
Made with ❤️

# 💬 Docker Chat App  
### _Developed & Modified by Eng. Muhammad Abdulghaffar_

![Docker Chat Screenshot](docs/screenshot.png)

---

## 🧩 Overview

**Docker Chat** is a real-time chat web application built with:
- 🐍 **Flask (Python)** — as the backend server  
- 🔥 **Flask-SocketIO** — for real-time messaging  
- 🗄️ **MySQL** — to store users and messages  
- 🌐 **Nginx** — as a reverse proxy  
- 🐳 **Docker Compose** — to orchestrate all services

Users can:
- Log in with username and password  
- Chat instantly with others (messages stored in DB)  
- See previous chat history  
- Run the entire system locally via Docker Compose  

---

## 🏗️ Project Structure

hello-docker-python/
│
├── app.py # Flask + SocketIO backend
├── Dockerfile # Build Flask container
├── docker-compose.yml # Define Flask, Nginx, MySQL
├── nginx.conf # Reverse proxy configuration
├── requirements.txt # Python dependencies
├── db-init/ # MySQL init scripts (tables & seed data)
├── templates/ # HTML (Bootstrap + SocketIO)
│ └── index.html
└── README.md # 📘 You are here

---

## ⚙️ How to Run Locally

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/docker-chat-app.git
cd docker-chat-app

docker compose up --build

Open Browser http://localhost:38080

Users: ahmed, mona, omar
Password: 123



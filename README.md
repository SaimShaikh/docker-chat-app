<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/3d67664b-ae53-47d9-842e-8ebf3da62678" />

---

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

* To check Containers
  ``docker ps -a ``
* To Check docker volumes
  ``docker volume ls``
---

* If you don’t known password use this
  ``docker exec chat-mysql <your db container name> printenv | grep MYSQL``
* To check Dataases in docker mysql
  ``docker exec -it chat-mysql <your db container name> bash``
> # login as root # enter: rootpass

<img width="3338" height="1107" alt="image" src="https://github.com/user-attachments/assets/329730f1-c6e1-4578-9731-ac9c63191f2d" />

```

SHOW DATABASES;
USE chatdb;
SHOW TABLES;

-- if you have a messages table, peek data:
SELECT * FROM messages ORDER BY id DESC LIMIT 20;

-- see table structure if needed
SHOW CREATE TABLE messages\G
```
<img width="1996" height="1357" alt="image" src="https://github.com/user-attachments/assets/b6887a9f-4315-41df-9ba0-b1aef470efb5" />


* Output:
> Register first 
<img width="3341" height="1837" alt="image" src="https://github.com/user-attachments/assets/5a12f763-2b7e-42e8-9800-358633ef8eb2" />
 
<img width="3314" height="1690" alt="image" src="https://github.com/user-attachments/assets/607dfed9-fe59-4b3e-992b-7f8a1509fedc" />


# Final app.py — Flask + Socket.IO + SQLAlchemy (MySQL-ready)
# Author: Eng. Muhammad Abdulghaffar

import os
from datetime import datetime

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------- App & DB Setup --------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecret")
# Use MySQL in Docker, fallback to local SQLite for dev
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///chat.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}

db = SQLAlchemy(app)

# eventlet is ideal with Flask-SocketIO for WS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# -------------------- Models --------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # nullable for old rows; new registrations will set it
    password = db.Column(db.String(255), nullable=True)
    # Optional created_at if your schema includes it
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# socket.id -> user.id map
sid_to_user = {}

# -------------------- HTTP Routes --------------------
@app.get("/")
def home():
    return render_template("index.html")

@app.get("/healthz")
def healthz():
    # Light DB ping; if DB unavailable, still return 200 so container can start
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pass
    return "ok", 200

# -------------------- Socket.IO Events --------------------
@socketio.on("connect")
def on_connect():
    emit("server_event", {"message": "Connected", "sid": request.sid})

@socketio.on("disconnect")
def on_disconnect():
    sid_to_user.pop(request.sid, None)

@socketio.on("register")
def register_user(data):
    username = (data or {}).get("username", "")
    password = (data or {}).get("password", "")

    username = (username or "").strip().lower()
    password = (password or "").strip()

    if not username or not password:
        emit("register_error", {"error": "username & password required"})
        return
    if len(username) > 50:
        emit("register_error", {"error": "username too long (<= 50)"})
        return

    if User.query.filter_by(username=username).first():
        emit("register_error", {"error": "username already exists"})
        return

    u = User(username=username, password=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()

    sid_to_user[request.sid] = u.id
    join_room(f"user:{u.id}")

    others = [x.username for x in User.query.filter(User.id != u.id).all()]
    emit("register_ok", {"me": u.username, "others": others})

@socketio.on("login")
def login_user(data):
    username = (data or {}).get("username", "")
    password = (data or {}).get("password", "")

    username = (username or "").strip().lower()
    password = (password or "").strip()

    if not username or not password:
        emit("login_error", {"error": "username & password required"})
        return

    user = User.query.filter_by(username=username).first()
    if not user or not user.password or not check_password_hash(user.password, password):
        emit("login_error", {"error": "invalid username or password"})
        return

    sid_to_user[request.sid] = user.id
    join_room(f"user:{user.id}")

    others = [u.username for u in User.query.filter(User.id != user.id).all()]
    emit("login_ok", {"me": user.username, "others": others})

@socketio.on("open_dialog")
def open_dialog(data):
    me_id = sid_to_user.get(request.sid)
    if not me_id:
        emit("login_error", {"error": "not logged in"})
        return

    other_name = (data or {}).get("with", "")
    other_name = (other_name or "").strip().lower()
    other = User.query.filter_by(username=other_name).first()
    if not other:
        emit("dialog_error", {"error": "user not found"})
        return

    msgs = (
        Message.query.filter(
            or_(
                (Message.sender_id == me_id) & (Message.receiver_id == other.id),
                (Message.sender_id == other.id) & (Message.receiver_id == me_id),
            )
        )
        .order_by(Message.id.asc())
        .limit(100)
        .all()
    )
    history = [
        {
            "from": ("me" if m.sender_id == me_id else "them"),
            "text": m.text,
            "at": m.created_at.isoformat(timespec="seconds"),
        }
        for m in msgs
    ]
    emit("history", {"with": other.username, "messages": history})

@socketio.on("chat_message")
def chat_message(data):
    me_id = sid_to_user.get(request.sid)
    if not me_id:
        emit("login_error", {"error": "not logged in"})
        return

    # Robust text parsing (fixes the accidental .trim() bug)
    raw_text = (data or {}).get("text", "")
    if raw_text is None:
        raw_text = ""
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)
    text_clean = raw_text.strip()

    to_name = (data or {}).get("to", "")
    if to_name is None:
        to_name = ""
    to_name = to_name.strip().lower()

    if not text_clean or not to_name:
        emit("send_error", {"error": "both 'to' and 'text' required"})
        return

    me = User.query.get(me_id)
    you = User.query.filter_by(username=to_name).first()
    if not you:
        emit("send_error", {"error": "recipient not found"})
        return

    msg = Message(sender_id=me.id, receiver_id=you.id, text=text_clean)
    db.session.add(msg)
    db.session.commit()

    payload = {
        "from": me.username,
        "to": you.username,
        "text": text_clean,
        "at": msg.created_at.isoformat(timespec="seconds"),
    }
    socketio.emit("chat_message", payload, room=f"user:{me.id}")
    socketio.emit("chat_message", payload, room=f"user:{you.id}")

# -------------------- Startup helpers --------------------
def ensure_password_column_if_mysql():
    """If running on MySQL and legacy table lacks 'password', add it."""
    with db.engine.connect() as conn:
        try:
            # Works on MySQL; ignored on SQLite
            res = conn.execute(text("SHOW COLUMNS FROM users LIKE 'password';"))
            exists = res.fetchone() is not None
            if not exists:
                conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NULL;"))
                conn.commit()
        except Exception:
            # SQLite or permission limited — ignore silently
            pass

if __name__ == "__main__":
    with app.app_context():
        # Safe with MySQL (tables pre-created by /docker-entrypoint-initdb.d),
        # and creates local tables for SQLite dev.
        db.create_all()
        ensure_password_column_if_mysql()
    # Match Nginx upstream (web:5000)
    socketio.run(app, host="0.0.0.0", port=5000)
# new 

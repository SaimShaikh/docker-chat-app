# Modified by Muhammad Abdulghaffar & Saime Shaikh
# Real-time chat app with register/login support for any user.

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# -------------------- App & DB Setup --------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///chat.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# -------------------- Models --------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

sid_to_user = {}

# -------------------- Routes --------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------- Socket Events --------------------
@socketio.on("register")
def register_user(data):
    username = (data or {}).get("username", "").strip().lower()
    password = (data or {}).get("password", "")
    if not username or not password:
        emit("register_error", {"error": "username & password required"})
        return

    if len(username) > 50:
        emit("register_error", {"error": "username too long"})
        return

    if User.query.filter_by(username=username).first():
        emit("register_error", {"error": "username already exists"})
        return

    hashed = generate_password_hash(password)
    u = User(username=username, password=hashed)
    db.session.add(u)
    db.session.commit()

    sid_to_user[request.sid] = u.id
    join_room(f"user:{u.id}")

    others = [x.username for x in User.query.filter(User.id != u.id).all()]
    emit("register_ok", {"me": u.username, "others": others})

@socketio.on("login")
def login_user(data):
    username = (data or {}).get("username", "").strip().lower()
    password = (data or {}).get("password", "")
    if not username or not password:
        emit("login_error", {"error": "username & password required"})
        return

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
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

    other_name = (data or {}).get("with", "").strip().lower()
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

    text_ = (data or {}).get("text", "").strip()
    to_name = (data or {}).get("to", "").strip().lower()
    if not text_ or not to_name:
        emit("send_error", {"error": "both 'to' and 'text' required"})
        return

    me = User.query.get(me_id)
    you = User.query.filter_by(username=to_name).first()
    if not you:
        emit("send_error", {"error": "recipient not found"})
        return

    msg = Message(sender_id=me.id, receiver_id=you.id, text=text_)
    db.session.add(msg)
    db.session.commit()

    payload = {
        "from": me.username,
        "to": you.username,
        "text": text_,
        "at": msg.created_at.isoformat(timespec="seconds"),
    }

    socketio.emit("chat_message", payload, room=f"user:{me.id}")
    socketio.emit("chat_message", payload, room=f"user:{you.id}")

@socketio.on("disconnect")
def disconnect_user():
    sid_to_user.pop(request.sid, None)

def ensure_password_column_only():
    with db.engine.connect() as conn:
        result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'password';"))
        exists = result.fetchone() is not None
        if not exists:
            print("🔧 Adding 'password' column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NULL;"))
            conn.commit()
    print("✅ Password column ensured")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_password_column_only()
    socketio.run(app, host='0.0.0.0', port=5000)

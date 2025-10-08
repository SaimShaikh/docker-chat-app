# Modified by Muhammad Abdulghaffar

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

# socket.id -> user.id map
sid_to_user = {}

# -------------------- Routes --------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------- Socket Events --------------------
@socketio.on("login")
def on_login(data):
    username = (data or {}).get("username", "").strip().lower()
    password = (data or {}).get("password", "")

    if not username or not password:
        emit("login_error", {"error": "username & password required"})
        return

    user = User.query.filter_by(username=username).first()
    if not user:
        emit("login_error", {"error": "user not found (use: ahmed, mona, omar)"})
        return

    if not user.password or not check_password_hash(user.password, password):
        emit("login_error", {"error": "invalid password"})
        return

    sid_to_user[request.sid] = user.id
    join_room(f"user:{user.id}")

    others = [u.username for u in User.query.filter(User.id != user.id).all()]
    emit("login_ok", {"me": user.username, "others": others})


@socketio.on("open_dialog")
def on_open_dialog(data):
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
def on_chat_message(data):
    me_id = sid_to_user.get(request.sid)
    if not me_id:
        emit("login_error", {"error": "not logged in"})
        return

    text = (data or {}).get("text", "").strip()
    to_name = (data or {}).get("to", "").strip().lower()
    if not text or not to_name:
        emit("send_error", {"error": "both 'to' and 'text' required"})
        return

    me = User.query.get(me_id)
    you = User.query.filter_by(username=to_name).first()
    if not you:
        emit("send_error", {"error": "recipient not found"})
        return

    msg = Message(sender_id=me.id, receiver_id=you.id, text=text)
    db.session.add(msg)
    db.session.commit()

    payload = {
        "from": me.username,
        "to": you.username,
        "text": text,
        "at": msg.created_at.isoformat(timespec="seconds"),
    }

    socketio.emit("chat_message", payload, room=f"user:{me.id}")
    socketio.emit("chat_message", payload, room=f"user:{you.id}")


@socketio.on("disconnect")
def on_disconnect():
    sid_to_user.pop(request.sid, None)

# -------------------- Auto DB Fix & Seed --------------------
def ensure_users_table_and_passwords():
    """
    """
    with db.engine.connect() as conn:
        result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'password';"))
        exists = result.fetchone() is not None
        if not exists:
            print("🔧 Adding 'password' column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NULL;"))
            conn.commit()

    # seed users + passwords
    default_users = ["ahmed", "mona", "omar"]
    for name in default_users:
        u = User.query.filter_by(username=name).first()
        if not u:
            u = User(username=name)
            db.session.add(u)
            db.session.commit()
        if not u.password:
            u.password = generate_password_hash("123")
            db.session.commit()
    print("✅ Users ensured with default password '123'")

# -------------------- Run --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_users_table_and_passwords()
    socketio.run(app, host='0.0.0.0', port=8080)

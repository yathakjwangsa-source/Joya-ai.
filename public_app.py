"""Authenticated web application for publicly hosting Joya."""

from __future__ import annotations

import json
import os
import random
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    g,
    jsonify,
    render_template_string,
    request,
    send_from_directory,
    session as web_session,
    stream_with_context,
)
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

import runpy


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
CORE_FILE = ROOT / "```python.py"
CORE = runpy.run_path(str(CORE_FILE), run_name="joya_core")
LOCAL_DATA_DIR = Path.home() / "JoyaAI"
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

database_url = os.environ.get("DATABASE_URL", "").strip()
if not database_url:
    database_url = f"sqlite:///{(LOCAL_DATA_DIR / 'joya_website.db').as_posix()}"
elif database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url.removeprefix("postgres://")
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

engine_options = {"pool_pre_ping": True}
if database_url.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(database_url, **engine_options)

metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(254), nullable=False, unique=True),
    Column("display_name", String(48), nullable=False),
    Column("password_hash", String(512), nullable=False),
    Column("created_at", String(32), nullable=False),
)
notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(120), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", String(32), nullable=False),
)
history = Table(
    "chat_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", String(32), nullable=False),
    Column("question", Text, nullable=False),
    Column("answer", Text, nullable=False),
)
progress = Table(
    "learning_progress",
    metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("jee_tests_completed", Integer, nullable=False, default=0),
    Column("jee_questions_correct", Integer, nullable=False, default=0),
    Column("jee_best_score", Integer, nullable=False, default=0),
)
active_tests = Table(
    "active_tests",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("questions_json", Text, nullable=False),
    Column("expires_at", Float, nullable=False),
)
metadata.create_all(engine)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=100_000,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("JOYASECURECOOKIES", "").lower()
    in {"1", "true", "yes"},
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "").strip() or CORE["OLLAMA_URL"]
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", CORE["OLLAMA_MODEL"])
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "").strip()
OLLAMA_TAGS_URL = OLLAMA_URL.rsplit("/api/", 1)[0] + "/api/tags"
JOYA_SYSTEM_PROMPT = CORE["JOYA_SYSTEM_PROMPT"]


def ollama_headers():
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    return headers


def login_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if not web_session.get("user_id"):
            return jsonify({"error": "Please sign in to continue."}), 401
        g.user_id = int(web_session["user_id"])
        return function(*args, **kwargs)

    return wrapped


def current_csrf_token() -> str:
    token = web_session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        web_session["_csrf_token"] = token
    return token


@app.before_request
def validate_csrf():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    expected = web_session.get("_csrf_token", "")
    provided = request.headers.get("X-CSRF-Token", "")
    if not expected or not secrets.compare_digest(expected, provided):
        return jsonify({"error": "Your session token expired. Reload and try again."}), 400
    return None


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self' data:; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "That request is too large."}), 413


@app.get("/")
def home():
    index_file = WEB_DIR / "index.html"
    return render_template_string(
        index_file.read_text(encoding="utf-8"),
        csrf_token=current_csrf_token(),
    )


@app.get("/app.css")
def stylesheet():
    return send_from_directory(WEB_DIR, "app.css")


@app.get("/app.js")
def javascript():
    return send_from_directory(WEB_DIR, "app.js")


@app.get("/logo.svg")
def logo():
    return send_from_directory(WEB_DIR, "logo.svg", mimetype="image/svg+xml")


@app.get("/manifest.webmanifest")
def web_manifest():
    return send_from_directory(
        WEB_DIR, "manifest.webmanifest", mimetype="application/manifest+json"
    )


@app.get("/service-worker.js")
def service_worker():
    response = send_from_directory(WEB_DIR, "service-worker.js")
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/me")
def get_current_user():
    user_id = web_session.get("user_id")
    if not user_id:
        return jsonify({
            "authenticated": False,
            "csrf_token": current_csrf_token(),
        })
    with engine.connect() as connection:
        user = connection.execute(
            select(users.c.id, users.c.email, users.c.display_name)
            .where(users.c.id == int(user_id))
        ).mappings().first()
    if user is None:
        web_session.clear()
        return jsonify({"authenticated": False, "csrf_token": current_csrf_token()})
    return jsonify({
        "authenticated": True,
        "email": user["email"],
        "name": user["display_name"],
        "csrf_token": current_csrf_token(),
    })


@app.patch("/api/me")
@login_required
def update_current_user():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 48:
        return jsonify({"error": "Name must be between 1 and 48 characters."}), 400
    name = name.strip()
    with engine.begin() as connection:
        connection.execute(
            update(users)
            .where(users.c.id == g.user_id)
            .values(display_name=name)
        )
    return jsonify({"name": name})


def rotate_login_session(user_id: int) -> str:
    web_session.clear()
    web_session.permanent = True
    web_session["user_id"] = user_id
    web_session["_csrf_token"] = secrets.token_urlsafe(32)
    return web_session["_csrf_token"]


@app.post("/api/auth/guest")
def create_guest_session():
    guest_id = secrets.token_urlsafe(24)
    try:
        with engine.begin() as connection:
            result = connection.execute(insert(users).values(
                email=f"guest-{guest_id}@guest.invalid",
                display_name="Learner",
                password_hash=generate_password_hash(secrets.token_urlsafe(48)),
                created_at=datetime.now().isoformat(timespec="seconds"),
            ))
            user_id = result.inserted_primary_key[0]
    except SQLAlchemyError:
        app.logger.exception("Guest session creation failed")
        return jsonify({"error": "Could not start a guest session. Please try again."}), 500

    token = rotate_login_session(int(user_id))
    return jsonify({
        "authenticated": True,
        "name": "Learner",
        "csrf_token": token,
        "guest": True,
    }), 201


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    name = payload.get("name", "")
    password = payload.get("password", "")
    if not all(isinstance(value, str) for value in (email, name, password)):
        return jsonify({"error": "Enter a valid name, email, and password."}), 400

    email = email.strip().lower()
    name = name.strip()
    if len(email) > 254 or "@" not in email or email.startswith("@") or email.endswith("@"):
        return jsonify({"error": "Enter a valid email address."}), 400
    if not name or len(name) > 48:
        return jsonify({"error": "Name must be between 1 and 48 characters."}), 400
    if len(password) < 10 or len(password) > 256:
        return jsonify({"error": "Use a password between 10 and 256 characters."}), 400

    try:
        with engine.begin() as connection:
            result = connection.execute(insert(users).values(
                email=email,
                display_name=name,
                password_hash=generate_password_hash(password),
                created_at=datetime.now().isoformat(timespec="seconds"),
            ))
            user_id = result.inserted_primary_key[0]
    except IntegrityError:
        return jsonify({"error": "An account with that email already exists."}), 409
    except SQLAlchemyError:
        app.logger.exception("Account registration failed")
        return jsonify({"error": "Account registration failed. Please try again."}), 500

    token = rotate_login_session(int(user_id))
    return jsonify({"authenticated": True, "name": name, "csrf_token": token}), 201


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Enter your email and password."}), 400
    email = email.strip().lower()
    with engine.connect() as connection:
        user = connection.execute(
            select(users).where(users.c.email == email)
        ).mappings().first()
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Email or password is incorrect."}), 401

    token = rotate_login_session(int(user["id"]))
    return jsonify({
        "authenticated": True,
        "name": user["display_name"],
        "csrf_token": token,
    })


@app.post("/api/auth/logout")
@login_required
def logout():
    web_session.clear()
    return jsonify({"ok": True})


@app.get("/api/status")
@login_required
def api_status():
    try:
        status_request = urllib.request.Request(
            OLLAMA_TAGS_URL,
            headers=ollama_headers(),
        )
        with urllib.request.urlopen(status_request, timeout=3) as response:
            installed_models = json.loads(response.read().decode("utf-8")).get("models", [])
        available = any(model.get("name") == OLLAMA_MODEL for model in installed_models)
        message = (
            f"Joya is ready with Ollama model {OLLAMA_MODEL}."
            if available
            else f"Install the Ollama model with: ollama pull {OLLAMA_MODEL}"
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        app.logger.info("Could not reach the configured Ollama service: %s", error)
        available = False
        message = "Check the configured Ollama service and make sure it is reachable."
    return jsonify({
        "available": available,
        "model": OLLAMA_MODEL,
        "message": message,
    })


@app.get("/api/bootstrap")
@login_required
def api_bootstrap():
    with engine.connect() as connection:
        note_count = connection.execute(
            select(func.count()).select_from(notes).where(notes.c.user_id == g.user_id)
        ).scalar_one()
        conversation_count = connection.execute(
            select(func.count()).select_from(history).where(history.c.user_id == g.user_id)
        ).scalar_one()
        stats = connection.execute(
            select(progress).where(progress.c.user_id == g.user_id)
        ).mappings().first()

    return jsonify({
        "app": CORE["BOT_NAME"],
        "lessons": len(CORE["LESSONS"]),
        "notes": note_count,
        "conversations": conversation_count,
        "jee_tests": stats["jee_tests_completed"] if stats else 0,
        "jee_correct": stats["jee_questions_correct"] if stats else 0,
    })


@app.get("/api/lessons")
@login_required
def api_lessons():
    return jsonify([
        {"topic": topic.title(), "content": content}
        for topic, content in CORE["LESSONS"].items()
    ])


@app.get("/api/notes")
@login_required
def api_notes():
    with engine.connect() as connection:
        result = connection.execute(
            select(notes.c.id, notes.c.title, notes.c.content, notes.c.created_at)
            .where(notes.c.user_id == g.user_id)
            .order_by(notes.c.id.desc())
        ).mappings().all()
    return jsonify([dict(row) for row in result])


@app.post("/api/notes")
@login_required
def api_add_note():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    content = payload.get("content", "")
    if not isinstance(title, str) or not isinstance(content, str):
        return jsonify({"error": "Note title and content must be text."}), 400
    title = title.strip()
    content = content.strip()
    if not title or not content:
        return jsonify({"error": "Add both a title and note content."}), 400
    if len(title) > 120 or len(content) > 10_000:
        return jsonify({"error": "Title limit is 120 characters; note limit is 10,000."}), 400

    with engine.begin() as connection:
        result = connection.execute(insert(notes).values(
            user_id=g.user_id,
            title=title,
            content=content,
            created_at=datetime.now().isoformat(timespec="seconds"),
        ))
        note_id = result.inserted_primary_key[0]
    return jsonify({
        "id": note_id,
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }), 201


@app.delete("/api/notes/<int:note_id>")
@login_required
def api_delete_note(note_id):
    with engine.begin() as connection:
        result = connection.execute(
            notes.delete().where(
                notes.c.id == note_id,
                notes.c.user_id == g.user_id,
            )
        )
    if result.rowcount != 1:
        return jsonify({"error": "That note was not found in your account."}), 404
    return jsonify({"ok": True})


@app.get("/api/history")
@login_required
def api_history():
    with engine.connect() as connection:
        result = connection.execute(
            select(
                history.c.created_at.label("time"),
                history.c.question.label("user"),
                history.c.answer.label("assistant"),
            )
            .where(history.c.user_id == g.user_id)
            .order_by(history.c.id.desc())
            .limit(20)
        ).mappings().all()
    return jsonify([dict(row) for row in reversed(result)])


def validate_chat_prompt():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        return None, (jsonify({"error": "Write a question before sending."}), 400)
    prompt = prompt.strip()
    if len(prompt) > 4000:
        return None, (jsonify({"error": "Please keep questions under 4,000 characters."}), 400)
    return prompt, None


def ollama_payload(prompt, stream=False):
    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": JOYA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": stream,
        "think": False,
        "options": {"temperature": 0.2, "num_predict": 768},
    }


def ollama_error_message(error):
    if isinstance(error, urllib.error.HTTPError) and error.code == 404:
        return f"Joya's Ollama model is missing. Install it with: ollama pull {OLLAMA_MODEL}"
    if isinstance(error, urllib.error.HTTPError) and error.code in {401, 403}:
        return "Ollama rejected the connection. Check the OLLAMA_API_KEY setting."
    if isinstance(error, urllib.error.URLError):
        return "Joya could not connect to the configured Ollama service."
    if isinstance(error, (TimeoutError, OSError)):
        return "Joya's request to Ollama timed out. Please try again."
    return "Ollama could not complete the request. Please try again."


@app.post("/api/chat")
@login_required
def api_chat():
    prompt, error = validate_chat_prompt()
    if error:
        return error
    try:
        ollama_request = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(ollama_payload(prompt)).encode("utf-8"),
            headers=ollama_headers(),
            method="POST",
        )
        with urllib.request.urlopen(ollama_request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
        message = result.get("message", {})
        answer = message.get("content") if isinstance(message, dict) else None
        if not answer:
            return jsonify({"error": "Joya returned an empty answer. Please try again."}), 502
        save_history(g.user_id, prompt, answer)
        return jsonify({"answer": answer})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        app.logger.warning("Ollama chat request failed: %s", error)
        return jsonify({"error": ollama_error_message(error)}), 503


def save_history(user_id: int, prompt: str, answer: str) -> None:
    with engine.begin() as connection:
        connection.execute(insert(history).values(
            user_id=user_id,
            created_at=datetime.now().isoformat(timespec="seconds"),
            question=prompt,
            answer=answer,
        ))
        old_ids = select(history.c.id).where(
            history.c.user_id == user_id
        ).order_by(history.c.id.desc()).offset(200)
        connection.execute(
            history.delete().where(
                history.c.user_id == user_id,
                history.c.id.in_(old_ids),
            )
        )


def sse_event(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
@login_required
def api_chat_stream():
    prompt, error = validate_chat_prompt()
    if error:
        return error

    def generate():
        answer_parts = []
        try:
            ollama_request = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(ollama_payload(prompt, stream=True)).encode("utf-8"),
                headers=ollama_headers(),
                method="POST",
            )
            with urllib.request.urlopen(ollama_request, timeout=180) as response:
                for line in response:
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    message = chunk.get("message", {})
                    token = message.get("content", "") if isinstance(message, dict) else ""
                    if not isinstance(token, str):
                        continue
                    if token:
                        answer_parts.append(token)
                        yield sse_event({"token": token})
                    if chunk.get("error"):
                        raise RuntimeError(chunk["error"])
            answer = "".join(answer_parts).strip()
            if not answer:
                yield sse_event({"error": "Joya returned an empty answer. Please try again."})
            else:
                try:
                    save_history(g.user_id, prompt, answer)
                except SQLAlchemyError:
                    app.logger.exception("Could not save chat history")
                    yield sse_event({"warning": "The answer arrived, but Joya could not save it to chat history."})
            yield sse_event({"done": True})
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as error:
            app.logger.warning("Ollama streaming request failed: %s", error)
            yield sse_event({"error": ollama_error_message(error)})

    return app.response_class(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/calculate")
@login_required
def api_calculate():
    payload = request.get_json(silent=True) or {}
    expression = payload.get("expression", "")
    if not isinstance(expression, str) or not expression.strip():
        return jsonify({"error": "Enter an arithmetic expression."}), 400
    try:
        answer = CORE["calculate"](expression.strip())
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError) as error:
        return jsonify({"error": f"Joya could not calculate that: {error}"}), 400
    return jsonify({"expression": expression.strip(), "answer": answer})


@app.get("/api/jee/questions")
@login_required
def api_start_test():
    level = request.args.get("level", "main")
    bank = CORE["JEE_QUESTIONS"]
    if level == "main":
        selected = [question for question in bank if question["level"] == "main"]
    elif level == "advanced":
        selected = [question for question in bank if question["level"] == "advanced"]
    elif level == "mock":
        selected = []
        for subject in ("Physics", "Chemistry", "Mathematics"):
            subject_questions = [q for q in bank if q["subject"] == subject]
            selected.extend(random.sample(subject_questions, 3))
        random.shuffle(selected)
    else:
        return jsonify({"error": "Choose Main, Advanced, or Mock."}), 400

    test_id = secrets.token_urlsafe(24)
    expires_at = time.time() + 3600
    with engine.begin() as connection:
        connection.execute(insert(active_tests).values(
            id=test_id,
            user_id=g.user_id,
            questions_json=json.dumps(selected, ensure_ascii=False),
            expires_at=expires_at,
        ))
        connection.execute(
            active_tests.delete().where(active_tests.c.expires_at < time.time())
        )

    public_questions = [
        {
            "subject": question["subject"],
            "level": question["level"],
            "question": question["question"],
            "options": question["options"],
        }
        for question in selected
    ]
    return jsonify({
        "test_id": test_id,
        "questions": public_questions,
        "duration_seconds": 30 * 60 if level == "mock" else None,
    })


@app.post("/api/jee/grade")
@login_required
def api_grade_test():
    payload = request.get_json(silent=True) or {}
    test_id = payload.get("test_id")
    answers = payload.get("answers")
    if not isinstance(test_id, str) or not isinstance(answers, list):
        return jsonify({"error": "Invalid test submission."}), 400

    with engine.begin() as connection:
        test = connection.execute(
            select(active_tests)
            .where(
                active_tests.c.id == test_id,
                active_tests.c.user_id == g.user_id,
            )
            .with_for_update()
        ).mappings().first()
        if test is None:
            return jsonify({"error": "This test expired or is already submitted. Start another test."}), 400
        if test["expires_at"] < time.time():
            connection.execute(
                active_tests.delete().where(active_tests.c.id == test_id)
            )
            return jsonify({"error": "This test expired. Start another practice test."}), 400

        selected = json.loads(test["questions_json"])
        if len(answers) != len(selected) or any(
            answer not in ("", "a", "b", "c", "d") for answer in answers
        ):
            return jsonify({"error": "Answers do not match this test."}), 400
        connection.execute(active_tests.delete().where(active_tests.c.id == test_id))

    results = []
    correct = incorrect = skipped = score = 0
    for question, answer in zip(selected, answers):
        if not answer:
            skipped += 1
            outcome = "Skipped"
        elif answer == question["answer"]:
            correct += 1
            score += 4
            outcome = "Correct"
        else:
            incorrect += 1
            score -= 1
            outcome = "Incorrect"
        results.append({
            "outcome": outcome,
            "selected": answer,
            "correct": question["answer"],
            "explanation": question["explanation"],
        })

    with engine.begin() as connection:
        stats = connection.execute(
            select(progress)
            .where(progress.c.user_id == g.user_id)
            .with_for_update()
        ).mappings().first()
        if stats is None:
            connection.execute(insert(progress).values(
                user_id=g.user_id,
                jee_tests_completed=1,
                jee_questions_correct=correct,
                jee_best_score=score,
            ))
        else:
            connection.execute(
                update(progress)
                .where(progress.c.user_id == g.user_id)
                .values(
                    jee_tests_completed=stats["jee_tests_completed"] + 1,
                    jee_questions_correct=stats["jee_questions_correct"] + correct,
                    jee_best_score=max(stats["jee_best_score"], score),
                )
            )

    return jsonify({
        "correct": correct,
        "incorrect": incorrect,
        "skipped": skipped,
        "score": score,
        "maximum_score": len(selected) * 4,
        "results": results,
    })


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return "Page not found.", 404


@app.errorhandler(500)
def server_error(_error):
    app.logger.exception("Unhandled server error")
    if request.path.startswith("/api/"):
        return jsonify({"error": "Joya encountered a server error. Please try again."}), 500
    return "Joya encountered a server error.", 500


def main() -> None:
    import threading
    import webbrowser

    threading.Timer(1.0, webbrowser.open, args=("http://127.0.0.1:8000",)).start()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=False)


if __name__ == "__main__":
    main()

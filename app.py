"""MedAI Hub - Medical Diagnosis System using AI and Machine Learning.

Run:  python app.py      ->  http://127.0.0.1:5000
"""
import datetime
import json
import os
import secrets
import sqlite3

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from ml import chatbot, risk_models, skin, symptom_model
from ml.knowledge import DISEASES, EMERGENCY_NUMBERS, RED_FLAGS, SYMPTOMS
from ml import wellness

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,          # 8 MB uploads
    DATABASE=os.environ.get("DATABASE", os.path.join(BASE, "instance", "medai.db")),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "bmp"}

TEAM = [
    ("Mohammed Faraz", "1AH22CS064"), ("Mohammed Saifulla", "1AH22CS105"),
    ("Mohammed Ayaan", "1AH23CS409"), ("Kashinath", "1AH22CS070"),
]


# ------------------------------------------------------------------ database
def db():
    if "db" not in g:
        os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def init_db():
    with app.app_context():
        db().executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS analyses(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            kind TEXT NOT NULL, summary TEXT NOT NULL, result_json TEXT NOT NULL,
            created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id));
        """)
        db().commit()


def save_analysis(kind, summary, result):
    """Store a result in the user's history (only when logged in)."""
    if not session.get("user_id"):
        return None
    slim = {k: v for k, v in result.items() if k != "overlay"}   # don't store images
    cur = db().execute(
        "INSERT INTO analyses(user_id, kind, summary, result_json, created_at) VALUES (?,?,?,?,?)",
        (session["user_id"], kind, summary, json.dumps(slim), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    db().commit()
    return cur.lastrowid


# ------------------------------------------------------------------ security
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.before_request
def csrf_protect():
    if request.method == "POST":
        sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
            abort(400, "Invalid or missing CSRF token. Refresh the page and try again.")


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


@app.template_filter("sin")
def sin_filter(x):
    import math
    return math.sin(x)


@app.context_processor
def inject():
    return {"csrf_token": csrf_token, "current_user": session.get("user_name"), "year": datetime.date.today().year}


@app.errorhandler(400)
@app.errorhandler(413)
@app.errorhandler(404)
def handle_err(e):
    msg = {413: "File too large (max 8 MB).", 404: "Page not found."}.get(e.code, getattr(e, "description", "Bad request"))
    if request.path.startswith("/api/"):
        return jsonify(error=msg), e.code
    return render_template("error.html", code=e.code, message=msg), e.code


# ------------------------------------------------------------------ pages
@app.route("/")
def index():
    return render_template("index.html", page="home", rec=wellness.todays_recommendation(),
                           stats={"diseases": len(DISEASES), "symptoms": len(SYMPTOMS)})


@app.route("/analysis")
def analysis():
    return render_template("analysis.html", page="analysis", symptoms=SYMPTOMS)


@app.route("/wellness")
def wellness_hub():
    return render_template("wellness.html", page="wellness", rec=wellness.todays_recommendation(),
                           workouts=wellness.WORKOUTS, diets=wellness.DIETS, focus=wellness.GENDER_FOCUS,
                           split=wellness.SPLIT)


@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html", page="chatbot")


@app.route("/about")
def about():
    return render_template("about.html", page="about", team=TEAM,
                           sm=symptom_model.metrics(), rm=risk_models.metrics(), diseases=DISEASES)


# ------------------------------------------------------------------ auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(pw) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "error")
        else:
            try:
                db().execute("INSERT INTO users(name,email,password_hash,created_at) VALUES (?,?,?,?)",
                             (name, email, generate_password_hash(pw), datetime.datetime.now().isoformat()))
                db().commit()
                flash("Account created - please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email is already registered.", "error")
    return render_template("auth.html", mode="register", page="login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        row = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row and check_password_hash(row["password_hash"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=row["id"], user_name=row["name"])
            flash(f"Welcome back, {row['name']}!", "success")
            return redirect(url_for("history"))
        flash("Invalid email or password.", "error")
    return render_template("auth.html", mode="login", page="login")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/history")
def history():
    if not session.get("user_id"):
        flash("Please log in to see your history.", "error")
        return redirect(url_for("login"))
    rows = db().execute("SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("history.html", rows=rows, page="login")


@app.route("/report/<int:rid>")
def report(rid):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    row = db().execute("SELECT * FROM analyses WHERE id=? AND user_id=?", (rid, session["user_id"])).fetchone()
    if not row:
        abort(404)
    return render_template("report.html", row=row, data=json.loads(row["result_json"]), page="login")


# ------------------------------------------------------------------ APIs
@app.post("/api/skin")
def api_skin():
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify(error="Please choose or capture an image first."), 400
    if f.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_EXT and not f.filename.startswith("capture"):
        return jsonify(error="Unsupported file type. Use JPG, PNG or WEBP."), 400
    try:
        result = skin.analyze(f.stream)
    except Exception:
        return jsonify(error="Could not read that image. Try a clear, well-lit photo."), 400
    result["history_id"] = save_analysis("Skin analysis", f"{result['top_prediction']} ({result['confidence']}%)", result)
    return jsonify(result)


@app.post("/api/symptoms")
def api_symptoms():
    data = request.get_json(silent=True) or {}
    present = {s for s in data.get("symptoms", []) if s in SYMPTOMS}
    if not present:
        return jsonify(error="Select at least one symptom."), 400
    ranked = symptom_model.predict(present)[:5]
    out = []
    for name, p in ranked:
        if p < 0.01:
            continue
        info = DISEASES[name]
        out.append({"disease": name, "probability": round(min(p, .97) * 100, 1), "severity": info["severity"],
                    "specialist": info["specialist"], "desc": info["desc"], "precautions": info["precautions"]})
    warning = next((m for combo, m in RED_FLAGS if combo <= present), None)
    result = {"predictions": out, "top_prediction": out[0]["disease"], "confidence": out[0]["probability"],
              "symptoms": sorted(present), "warning": warning, "emergency": EMERGENCY_NUMBERS if warning else None}
    result["history_id"] = save_analysis("Symptom check", f"{out[0]['disease']} ({out[0]['probability']}%)", result)
    return jsonify(result)


def _risk_endpoint(name, title):
    data = request.get_json(silent=True) or {}
    result, errors = risk_models.predict(name, data)
    if errors:
        return jsonify(error="; ".join(errors)), 400
    result["top_prediction"] = f"{result['category']} risk"
    result["confidence"] = result["risk_percent"]
    result["history_id"] = save_analysis(title, f"{result['category']} risk ({result['risk_percent']}%)", result)
    return jsonify(result)


@app.post("/api/diabetes")
def api_diabetes():
    return _risk_endpoint("diabetes", "Diabetes risk")


@app.post("/api/heart")
def api_heart():
    return _risk_endpoint("heart", "Heart-disease risk")


@app.post("/api/bmi")
def api_bmi():
    d = request.get_json(silent=True) or {}
    try:
        w, h, a = float(d["weight"]), float(d["height"]), float(d["age"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Enter weight, height and age."), 400
    if not (20 <= w <= 300 and 100 <= h <= 250 and 10 <= a <= 100):
        return jsonify(error="Values look out of range."), 400
    return jsonify(wellness.bmi_report(w, h, a, d.get("sex", "male"), d.get("activity", "light")))


@app.post("/api/chat/start")
def api_chat_start():
    state, msgs = chatbot.start()
    session["chat"] = state
    return jsonify(messages=msgs)


@app.post("/api/chat")
def api_chat():
    text = (request.get_json(silent=True) or {}).get("message", "")[:500]
    state = session.get("chat") or chatbot.start()[0]
    state, msgs, meta = chatbot.reply(state, text)
    session["chat"] = state
    if meta.get("type") == "result" and session.get("user_id"):
        r = state["result"]
        save_analysis("Chatbot", f"{r['disease']} ({r['confidence']}%)", {"chat_result": r, "symptoms": state["present"]})
    return jsonify(messages=msgs, meta=meta)


@app.get("/health")
def health():
    return jsonify(status="ok")


init_db()
# make sure models exist before the first request
symptom_model.load()
risk_models.metrics()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))

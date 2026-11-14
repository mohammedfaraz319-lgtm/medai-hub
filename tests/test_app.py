import io
import os
import sys
import tempfile

import pytest
from PIL import Image, ImageDraw

os.environ["DATABASE"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as medai  # noqa: E402
from ml import chatbot, risk_models, symptom_model  # noqa: E402


@pytest.fixture()
def client():
    medai.app.config["TESTING"] = True
    with medai.app.test_client() as c:
        yield c


def token(c):
    c.get("/")
    with c.session_transaction() as s:
        return s["csrf"]


def post(c, url, **kw):
    return c.post(url, headers={"X-CSRF-Token": token(c)}, **kw)


def test_pages_load(client):
    for url in ["/", "/analysis", "/wellness", "/chatbot", "/about", "/login", "/register", "/health"]:
        assert client.get(url).status_code == 200, url


def test_csrf_blocks_post_without_token(client):
    assert client.post("/api/symptoms", json={"symptoms": ["fever"]}).status_code == 400


def test_symptom_model_accuracy():
    assert symptom_model.metrics()["accuracy"] > 0.8


def test_symptom_prediction_sensible():
    top = symptom_model.predict({"wheezing", "shortness_of_breath"})[0][0]
    assert "Asthma" in top
    top = symptom_model.predict({"burning_urination", "frequent_urination"})[0][0]
    assert "UTI" in top


def test_symptoms_api(client):
    r = post(client, "/api/symptoms", json={"symptoms": ["sneezing", "runny_nose", "itchy_eyes"]})
    assert r.status_code == 200
    assert r.json["top_prediction"] == "Allergic Rhinitis"
    assert post(client, "/api/symptoms", json={"symptoms": []}).status_code == 400


def test_risk_models_direction():
    low, _ = risk_models.predict("diabetes", dict(age=25, bmi=22, glucose=85, systolic_bp=110, family_history=0, activity_days=5))
    high, _ = risk_models.predict("diabetes", dict(age=60, bmi=34, glucose=180, systolic_bp=150, family_history=1, activity_days=0))
    assert high["risk_percent"] > low["risk_percent"] + 30
    h_low, _ = risk_models.predict("heart", dict(age=30, male=0, systolic_bp=110, cholesterol=160, smoker=0, diabetic=0, bmi=22, activity_days=5, family_history=0))
    h_high, _ = risk_models.predict("heart", dict(age=70, male=1, systolic_bp=170, cholesterol=290, smoker=1, diabetic=1, bmi=33, activity_days=0, family_history=1))
    assert h_high["risk_percent"] > h_low["risk_percent"] + 30


def test_risk_validation(client):
    r = post(client, "/api/diabetes", json={"age": 999})
    assert r.status_code == 400


def test_skin_api(client):
    img = Image.new("RGB", (300, 300), (233, 190, 170))
    ImageDraw.Draw(img).ellipse((90, 90, 210, 210), fill=(110, 60, 40))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    buf.seek(0)
    r = post(client, "/api/skin", data={"image": (buf, "mole.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.json["segmented"] is True
    assert abs(sum(x["prob"] for x in r.json["ranked"]) - 100) < 1
    assert r.json["overlay"].startswith("data:image/png")


def test_skin_rejects_bad_file(client):
    r = post(client, "/api/skin", data={"image": (io.BytesIO(b"not an image"), "x.txt")}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_chatbot_flow():
    state, _ = chatbot.start()
    state, msgs, _ = chatbot.reply(state, "I have fever, headache and body pain")
    for _ in range(8):
        if state["stage"] == "doctor":
            break
        state, msgs, _ = chatbot.reply(state, "yes")
    assert state["stage"] == "doctor"
    state, msgs, _ = chatbot.reply(state, "y")
    assert "consider seeing" in msgs[0]


def test_chatbot_negation():
    present, absent = chatbot.extract("I have cough but no fever")
    assert "cough" in present and "fever" in absent


def test_auth_and_history(client):
    t = token(client)
    client.post("/register", data={"name": "Test User", "email": "t@example.com", "password": "password123", "csrf_token": t})
    client.post("/login", data={"email": "t@example.com", "password": "password123", "csrf_token": t})
    r = post(client, "/api/symptoms", json={"symptoms": ["fever", "chills", "sweating"]})
    assert r.json["history_id"]
    assert b"Symptom check" in client.get("/history").data
    assert client.get(f"/report/{r.json['history_id']}").status_code == 200


def test_wellness_bmi(client):
    r = post(client, "/api/bmi", json={"weight": 70, "height": 175, "age": 22, "sex": "male", "activity": "light"})
    assert r.status_code == 200 and 22 < r.json["bmi"] < 23

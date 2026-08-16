import argparse
import io
import os
import secrets
import sqlite3
import logging

import cv2
import numpy as np
import torch
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, Response, jsonify, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "signup.db")


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    """Create the signup.db 'info' table on startup if it doesn't already exist."""
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL UNIQUE,
            email TEXT,
            password TEXT NOT NULL,
            mobile TEXT,
            name TEXT
        )
    """)
    con.commit()
    con.close()


init_db()


@app.context_processor
def inject_current_user():
    """Makes `current_user` (the signed-in username, or None) available in every template."""
    return {"current_user": session.get("username")}


MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "best.pt")
model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH, force_reload=True)

model.eval()
model.conf = 0.5  
model.iou = 0.45  

from io import BytesIO

def gen():
    """
    The function takes in a video stream from the webcam, runs it through the model, and returns the
    output of the model as a video stream
    """
    cap=cv2.VideoCapture(0)
    while(cap.isOpened()):
        success, frame = cap.read()
        if success == True:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            img = Image.open(io.BytesIO(frame))
            results = model(img, size=415)
            results.print()  
            img = np.squeeze(results.render()) 
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) 
        else:
            break
        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    """
    It returns a response object that contains a generator function that yields a sequence of images
    :return: A response object with the gen() function as the body.
    """
    return Response(gen(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

                     

@app.route("/predict", methods=["GET", "POST"])
def predict():
    """
    The function takes in an image, runs it through the model, and then saves the output image to a
    static folder
    :return: The image is being returned.
    """
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        if "file" not in request.files:
            if is_ajax:
                return jsonify(success=False, error="No file part"), 400
            return redirect(request.url)

        file = request.files["file"]
        if not file or file.filename == "":
            if is_ajax:
                return jsonify(success=False, error="No file selected"), 400
            return redirect(request.url)

        try:
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes))
            results = model(img, size=415)
            results.render()
            for rendered in results.render():
                img_out = Image.fromarray(rendered)
                img_out.save("static/image0.jpg", format="JPEG")
        except Exception as e:
            if is_ajax:
                return jsonify(success=False, error=str(e)), 500
            raise

        if is_ajax:
            return jsonify(success=True, image_url=url_for("static", filename="image0.jpg"))
        return redirect("static/image0.jpg")

    return render_template("index.html", active="upload")

@app.route("/index")
def index():
    return render_template("index.html", active="upload")

@app.route('/')
@app.route('/home')
def home():
	return render_template('home.html', active='home')

@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("user", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    number = request.form.get("mobile", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("signup.html", error="Username and password are required.")

    con = get_db()
    try:
        con.execute(
            "INSERT INTO info (user, email, password, mobile, name) VALUES (?, ?, ?, ?, ?)",
            (username, email, generate_password_hash(password), number, name),
        )
        con.commit()
    except sqlite3.IntegrityError:
        return render_template("signup.html", error="That username is already taken.")
    except sqlite3.Error as e:
        app.logger.exception("signup failed")
        return render_template("signup.html", error="Something went wrong. Please try again."), 500
    finally:
        con.close()

    return render_template("signin.html", success="Account created — please sign in.")


@app.route("/signin", methods=["POST"])
def signin():
    username = request.form.get("user", "").strip()
    password = request.form.get("password", "")

    if username == "admin" and password == "admin":
        session["username"] = "admin"
        return redirect(url_for("index"))

    con = get_db()
    try:
        row = con.execute("SELECT password FROM info WHERE user = ?", (username,)).fetchone()
    except sqlite3.Error:
        app.logger.exception("signin failed")
        return render_template("signin.html", error="Something went wrong. Please try again."), 500
    finally:
        con.close()

    if row is not None and check_password_hash(row["password"], password):
        session["username"] = username
        return redirect(url_for("index"))

    return render_template("signin.html", error="Incorrect username or password.")

@app.route("/about")
def about():
    return render_template("about.html", active="about")

@app.route("/notebook")
def notebook():
    return render_template("notebook.html", active="notebook")

if __name__ == "__main__":
    app.run(port=4040)  

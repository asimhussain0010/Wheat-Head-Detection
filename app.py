
import argparse
import io
import os
from PIL import Image
import cv2
import numpy as np
from torchvision.models import detection
import sqlite3
import torch
from torchvision import models
from flask import Flask, render_template, request, redirect, Response, jsonify, url_for

app = Flask(__name__)


def init_db():
    """Create the signup.db 'info' table on startup if it doesn't already exist."""
    con = sqlite3.connect("signup.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            mobile TEXT,
            name TEXT
        )
    """)
    con.commit()
    con.close()


init_db()


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

@app.route("/signup")
def signup():

    username = request.args.get('user','')
    name = request.args.get('name','')
    email = request.args.get('email','')
    number = request.args.get('mobile','')
    password = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
    con.commit()
    con.close()
    return render_template("signin.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('user','')
    password1 = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        return render_template("signin.html")    

    elif mail1 == 'admin' and password1 == 'admin':
        return render_template("index.html")

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("index.html")
    else:
        return render_template("signup.html")

@app.route("/about")
def about():
    return render_template("about.html", active="about")

@app.route("/notebook")
def notebook():
    return render_template("notebook.html", active="notebook")

if __name__ == "__main__":
    app.run(port=4040)  

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# DB 기본 코드
import os
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    image1 = db.Column(db.String(100), nullable=False)
    image2 = db.Column(db.String(100), nullable=False)
    image3 = db.Column(db.String(100), nullable=False)
    image4 = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    background = db.Column(db.String(100), nullable=False)
    shared = db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template('main.html')

@app.route("/create")
def create_frame():
    return render_template('frame.html')

@app.route("/api/upload", methods=['POST'])
def photo_upload():

    image1 = request.files.get("photos", None)
    image2 = request.files.get("photos", None)
    image3 = request.files.get("photos", None)
    image4 = request.files.get("photos", None)

    # Save the images to a directory or process them as needed
    # For example, you can save them to a folder using the save() method
    image1.save(os.path.join(app.config['UPLOAD_FOLDER'], image1.filename))
    image2.save(os.path.join(app.config['UPLOAD_FOLDER'], image2.filename))
    image3.save(os.path.join(app.config['UPLOAD_FOLDER'], image3.filename))
    image4.save(os.path.join(app.config['UPLOAD_FOLDER'], image4.filename))

    # Create a new Image object and save it to the database
    image = Image(
        user_id=1,  # Replace with the actual user ID
        image1=image1.filename,
        image2=image2.filename,
        image3=image3.filename,
        image4=image4.filename,
        type="type_placeholder",
        background="background_placeholder",
        shared=False
    )
    db.session.add(image)
    db.session.commit()
    return redirect(url_for('create_frame'))
if __name__ == "__main__":
    app.run(debug=True)
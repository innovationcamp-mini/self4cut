from flask_sqlalchemy import SQLAlchemy
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
from config import CLIENT_ID, REDIRECT_URI, SECRET_KEY
import requests

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)


# 카카오 설정
KAKAO_OAUTH_URL = 'https://kauth.kakao.com/oauth/authorize'
KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_PROFILE_URL = 'https://kapi.kakao.com/v2/user/me'

# DB 기본 코드
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kakao_id = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=False)


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


@app.route('/')
def home():
    if 'kakao_id' in session:
        return redirect(url_for('profile'))
    return render_template('onboarding.html')


@app.route('/login')
def login():
    kakao_login_url = f"{KAKAO_OAUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    return redirect(kakao_login_url)


@app.route('/oauth')
def oauth():
    code = request.args.get('code')
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'code': code,
    }
    token_response = requests.post(KAKAO_TOKEN_URL, data=token_data)
    token_json = token_response.json()

    if token_response.status_code != 200:
        return f"Error getting token: {token_response.status_code}, {token_json}"

    access_token = token_json['access_token']
    profile_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    profile_response = requests.get(KAKAO_PROFILE_URL, headers=profile_headers)
    profile_json = profile_response.json()

    if profile_response.status_code != 200:
        return f"Error getting profile: {profile_response.status_code}, {profile_json}"

    kakao_id = profile_json['id']
    nickname = profile_json.get('properties', {}).get('nickname')

    user = Users.query.filter_by(kakao_id=kakao_id).first()
    if not user:
        new_user = Users(kakao_id=kakao_id, nickname=nickname)
        db.session.add(new_user)
        db.session.commit()

    session['kakao_id'] = kakao_id
    session['nickname'] = nickname

    session.permanent = True
    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    return redirect(url_for('create_frame'))


@app.route('/profile')
def profile():
    if 'kakao_id' not in session:
        return redirect(url_for('home'))
    return render_template('main.html', nickname=session['nickname'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/main')
def main():
    if 'kakao_id' not in session or 'nickname' not in session:
        return redirect(url_for('create_frame'))
    return render_template('main.html', nickname=session['nickname'])


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
    app.run(debug=True,host='0.0.0.0', port=5001,)
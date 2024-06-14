from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from config import CLIENT_ID, REDIRECT_URI, SECRET_KEY

app = Flask(__name__) 
CORS(app)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB 파일 크기 제한

# 카카오 설정
KAKAO_OAUTH_URL = 'https://kauth.kakao.com/oauth/authorize'
KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_PROFILE_URL = 'https://kapi.kakao.com/v2/user/me'


# 업로드 폴더 생성 확인
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# DB 설정 및 모델 정의
from flask_sqlalchemy import SQLAlchemy

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
    token_response = request.post(KAKAO_TOKEN_URL, data=token_data)
    token_json = token_response.json()

    if token_response.status_code != 200:
        return f"Error getting token: {token_response.status_code}, {token_json}"

    access_token = token_json['access_token']
    profile_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    profile_response = request.get(KAKAO_PROFILE_URL, headers=profile_headers)
    profile_json = profile_response.json()

    if profile_response.status_code != 200:
        return f"Error getting profile: {profile_response.status_code}, {profile_json}"

    kakao_id = profile_json['id']
    nickname = profile_json.get('properties', {}).get('nickname')

    user = Users.query.filter_by(kakao_id=kakao_id).first()
    if not user:
        user = Users(kakao_id=kakao_id, nickname=nickname)
        db.session.add(user)
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
        return redirect(url_for('home'))
    return render_template('main.html', nickname=session['nickname'])

@app.route("/create")
def create_frame():
    return render_template('frame.html')

@app.route("/select")
def select_frame():
    frame_list = Image.query.all() # 모든 이미지를 가져옴
    return render_template('select.html', data=frame_list)

@app.route("/api/upload", methods=['POST'])
def photo_upload():
    images = request.files.getlist("photos")
    if len(images) != 8:
        return jsonify({"error": "4개의 이미지를 업로드해주세요."}), 400

    filenames = []
    for image in images:
        if image:
            filename = secure_filename(image.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image.save(file_path)
            filenames.append(unique_filename)

    # 예시: 사용자 ID를 세션에서 가져온다고 가정
    user_id = session.get('user_id', 1)  # 실제 사용자 ID로 수정하세요

    image_record = Image(
        user_id=user_id,
        image1=filenames[0],
        image2=filenames[1],
        image3=filenames[2],
        image4=filenames[3],
        type=request.form.get("section"),
        background=request.form.get("frameColor"),
        shared=False
    )
    db.session.add(image_record)
    db.session.commit()

    return jsonify({"message": "이미지가 성공적으로 업로드되었습니다."})

if __name__ == "__main__":
    app.run(debug=True)
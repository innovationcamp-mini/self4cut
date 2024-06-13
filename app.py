from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import requests
from config import CLIENT_ID, SECRET_KEY, REDIRECT_URI

# 로그인
app = Flask(__name__)
app.config.from_pyfile('config.py')


def get_db():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    return conn


# 카카오 설정
KAKAO_OAUTH_URL = 'https://kauth.kakao.com/oauth/authorize'
KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_PROFILE_URL = 'https://kapi.kakao.com/v2/user/me'


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                kakao_id TEXT,
                nickname TEXT
            )
        ''')
        db.commit()


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

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE kakao_id = ?', (kakao_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            'INSERT INTO users (kakao_id, email, nickname) VALUES (?, ?, ?)', (kakao_id, nickname))
        db.commit()

    session['kakao_id'] = kakao_id
    session['nickname'] = nickname

    session.permanent = True
    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    return redirect(url_for('main'))


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

@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)

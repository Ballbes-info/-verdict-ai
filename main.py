from flask import Flask, render_template, request, session, redirect, url_for
from functools import wraps
from data.user import User
import json
import random
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import smtplib
import os
import io
import base64
from email.message import EmailMessage
from authlib.integrations.flask_client import OAuth
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 МБ на загрузку

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

db_session.global_init('db/blogs.db')



def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def set_user_session(user):
    session['user_id'] = user.id
    session['email'] = user.email
    session['user_name'] = user.user_name


def process_avatar(file_storage):
    """Открывает загруженный файл, делает квадратный кроп по центру,
    сжимает до 256x256 и возвращает data-URI для хранения в БД."""
    img = Image.open(file_storage.stream)
    img = img.convert('RGB')

    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((256, 256), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{encoded}'


@app.context_processor
def inject_current_user():
    if 'user_id' not in session:
        return {'current_user': None}
    ses = db_session.create_session()
    user = ses.query(User).filter(User.id == session['user_id']).first()
    ses.close()
    return {'current_user': user}


@app.route("/", methods=["POST", "GET"])
def welcome():
    if 'user_id' in session:
        return redirect('/select_mode')

    if request.method == "POST":
        ses = db_session.create_session()
        email = request.form.get('email', '').strip()
        user = ses.query(User).filter(User.email == email).first()
        ses.close()

        if user:
            passw = user.password
            if passw and check_password_hash(passw, request.form.get('password')):
                set_user_session(user)
                return redirect('/select_mode')

        return render_template("welcome.html", login_error=True)

    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    email = request.args.get("email", "")
    password = request.args.get("password", "")
    return render_template("login.html", email=email, password=password)


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user_id' in session:
        return redirect('/select_mode')

    if request.method == "GET":
        return render_template('register.html', error=None, step=1)

    step = request.form.get('action')
    if step == 'first_step':
        email = request.form.get('email', '').strip()
        ses = db_session.create_session()
        user = ses.query(User).filter(User.email == email).first()
        ses.close()

        if user:
            return render_template('register.html', error=None, email_in=1, passw_error=0, step=1)

        passs = request.form.get('pass')
        rep_pass = request.form.get('repid_pass')
        if passs != rep_pass:
            return render_template('register.html', error=None, email_in=0, passw_error=1, step=1)

        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        if not gmail_user or not gmail_password:
            app.logger.error("GMAIL_USER / GMAIL_PASSWORD не заданы — письмо не отправлено")
            return render_template('register.html', error=None, email_in=0,
                                   passw_error=0, mail_error=1, step=1)

        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        try:
            msg = EmailMessage()
            msg.set_content(f"Код подтверждения: {code}")
            msg["Subject"] = f"Код подтверждения BARAVKO: {code}"
            msg["From"] = gmail_user
            msg["To"] = email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.send_message(msg)
        except Exception as e:
            app.logger.error(f"Не удалось отправить письмо на {email}: {e}")
            return render_template('register.html', error=None, email_in=0,
                                   passw_error=0, mail_error=1, step=1)

        session['reg_code'] = generate_password_hash(code)
        session['reg_email'] = email
        session['reg_password'] = generate_password_hash(passs)

        return render_template('register.html', step=2)

    else:
        input_code = request.form.get('full_code')
        real_code = session.get('reg_code')
        if not real_code or not check_password_hash(real_code, input_code):
            return render_template('register.html', step=2, code_error=True)

        with open("nicknames.json", mode='r', encoding='utf-8') as f:
            nicknames_data = json.load(f)

        ses = db_session.create_session()
        while True:
            nick_name = f'{random.choice(nicknames_data)}{random.randint(1, 1000000000)}'
            if not ses.query(User).filter(User.user_name == nick_name).first():
                break

        new_user = User()
        new_user.email = session['reg_email']
        new_user.user_name = nick_name
        new_user.password = session['reg_password']
        ses.add(new_user)
        ses.commit()

        set_user_session(new_user)

        session.pop('reg_code', None)
        session.pop('reg_email', None)
        session.pop('reg_password', None)

        ses.close()
        return redirect('/select_mode')


@app.route('/auth/google')
def auth_google():
    redirect_uri = url_for('auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def auth_google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        return redirect('/')

    google_id = user_info['sub']
    email = user_info['email']

    ses = db_session.create_session()
    user = ses.query(User).filter(User.google_id == google_id).first()

    if not user:
        user = ses.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            with open("nicknames.json", mode='r', encoding='utf-8') as f:
                nicknames_data = json.load(f)
            while True:
                nick_name = f'{random.choice(nicknames_data)}{random.randint(1, 1000000000)}'
                if not ses.query(User).filter(User.user_name == nick_name).first():
                    break
            user = User()
            user.email = email
            user.google_id = google_id
            user.user_name = nick_name
            ses.add(user)
        ses.commit()
        ses.refresh(user)

    set_user_session(user)
    ses.close()
    return redirect('/select_mode')


@app.route('/profile')
@login_required
def profile():
    ses = db_session.create_session()
    user = ses.query(User).filter(User.id == session['user_id']).first()
    ses.close()
    if not user:
        session.clear()
        return redirect('/')
    return render_template(
        'profile.html',
        profile_user=user,
        has_password=bool(user.password),
        via_google=bool(user.google_id),
        status=request.args.get('status'),
    )


@app.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')
    if not file or file.filename == '':
        return redirect('/profile?status=nofile')

    try:
        data_uri = process_avatar(file)
    except Exception:
        return redirect('/profile?status=badimage')

    ses = db_session.create_session()
    user = ses.query(User).filter(User.id == session['user_id']).first()
    user.avatar = data_uri
    ses.commit()
    ses.close()
    return redirect('/profile?status=saved')


@app.route('/profile/avatar/delete', methods=['POST'])
@login_required
def delete_avatar():
    ses = db_session.create_session()
    user = ses.query(User).filter(User.id == session['user_id']).first()
    user.avatar = None
    ses.commit()
    ses.close()
    return redirect('/profile?status=removed')


@app.route("/court")
@login_required
def court():
    return render_template('court.html')


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")


@app.route('/select_mode')
@login_required
def select_mode():
    return render_template('modes.html')


if __name__ == "__main__":
    app.run(debug=True)

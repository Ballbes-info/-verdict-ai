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
import ssl
from email.message import EmailMessage
from authlib.integrations.flask_client import OAuth
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

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


def send_email(to_email, subject, body):
    smtp_server = os.getenv('GMAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('GMAIL_PORT', 465))
    smtp_username = os.getenv('GMAIL_USERNAME')
    smtp_password = os.getenv('GMAIL_PASSWORD')

    if not smtp_username or not smtp_password:
        app.logger.error("GMAIL_USERNAME / GMAIL_PASSWORD не заданы")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_username
        msg["To"] = to_email
        msg.set_content(body)

        context = ssl.create_default_context()

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

        return True
    except Exception as e:
        app.logger.error(f"Ошибка отправки письма: {e}")
        return False


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

    reset_success = request.args.get('reset_success', False)
    return render_template("welcome.html", reset_success=reset_success)


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
            return render_template('register.html', error="Этот email уже зарегистрирован", email_in=1, passw_error=0,
                                   step=1)

        passs = request.form.get('pass')
        rep_pass = request.form.get('repid_pass')
        if passs != rep_pass:
            return render_template('register.html', error="Пароли не совпадают", email_in=0, passw_error=1, step=1)

        if len(passs) < 6:
            return render_template('register.html', error="Пароль должен быть не менее 6 символов", email_in=0,
                                   passw_error=1, step=1)

        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        subject = "Код подтверждения BinaryClash"
        body = f"Ваш код подтверждения: {code}"

        if not send_email(email, subject, body):
            return render_template('register.html', error="Не удалось отправить письмо", email_in=0,
                                   passw_error=0, mail_error=1, step=1)

        session['reg_code'] = generate_password_hash(code)
        session['reg_email'] = email
        session['reg_password'] = generate_password_hash(passs)
        session['reg_code_time'] = datetime.now().timestamp()
        session['reg_last_sent'] = datetime.now().timestamp()

        return render_template('register.html', step=2, email=email)

    else:
        input_code = request.form.get('full_code')
        real_code = session.get('reg_code')

        if not real_code:
            return render_template('register.html', step=2, code_error=True, error="Сессия истекла")

        code_time = session.get('reg_code_time', 0)
        if datetime.now().timestamp() - code_time > 600:
            session.pop('reg_code', None)
            session.pop('reg_email', None)
            session.pop('reg_password', None)
            session.pop('reg_code_time', None)
            session.pop('reg_last_sent', None)
            return render_template('register.html', step=1, error="Время подтверждения истекло")

        if not check_password_hash(real_code, input_code):
            return render_template('register.html', step=2, code_error=True)

        ses = db_session.create_session()
        email = session.get('reg_email')
        existing_user = ses.query(User).filter(User.email == email).first()

        if existing_user:
            ses.close()
            session.pop('reg_code', None)
            session.pop('reg_email', None)
            session.pop('reg_password', None)
            session.pop('reg_code_time', None)
            session.pop('reg_last_sent', None)
            return render_template('register.html', step=1, error="Этот email уже зарегистрирован")

        with open("nicknames.json", mode='r', encoding='utf-8') as f:
            nicknames_data = json.load(f)

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
        session.pop('reg_code_time', None)
        session.pop('reg_last_sent', None)

        ses.close()
        return redirect('/select_mode')


@app.route("/resend_code", methods=["POST"])
def resend_code():
    """Повторная отправка кода подтверждения"""
    email = session.get('reg_email')
    if not email:
        return {'error': 'Сессия истекла'}, 400

    last_sent = session.get('reg_last_sent', 0)
    if datetime.now().timestamp() - last_sent < 120:
        remaining = 120 - int(datetime.now().timestamp() - last_sent)
        return {'error': f'Подождите {remaining} секунд перед повторной отправкой'}, 429

    code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    session['reg_code'] = generate_password_hash(code)
    session['reg_code_time'] = datetime.now().timestamp()
    session['reg_last_sent'] = datetime.now().timestamp()

    subject = "Код подтверждения BinaryClash"
    body = f"Ваш код подтверждения: {code}"

    if send_email(email, subject, body):
        return {'success': True}
    else:
        return {'error': 'Не удалось отправить письмо'}, 500


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if 'user_id' in session:
        return redirect('/select_mode')

    if request.method == "GET":
        return render_template('reset_password.html', step=1)

    step = request.form.get('action')

    if step == 'request':
        email = request.form.get('email', '').strip()

        ses = db_session.create_session()
        user = ses.query(User).filter(User.email == email).first()
        ses.close()

        if not user:
            return render_template('reset_password.html', step=1, error="Пользователь с таким email не найден")

        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        subject = "Восстановление пароля BinaryClash"
        body = f"Ваш код для восстановления пароля: {code}"

        if not send_email(email, subject, body):
            return render_template('reset_password.html', step=1,
                                   error="Не удалось отправить письмо. Попробуйте позже.")

        session['reset_code'] = generate_password_hash(code)
        session['reset_email'] = email
        session['reset_code_time'] = datetime.now().timestamp()
        session['reset_last_sent'] = datetime.now().timestamp()

        return render_template('reset_password.html', step=2, email=email)

    elif step == 'verify':
        input_code = request.form.get('full_code')
        real_code = session.get('reset_code')
        email = session.get('reset_email')

        if not real_code:
            return render_template('reset_password.html', step=1,
                                   error="Сессия истекла. Начните восстановление заново.")

        code_time = session.get('reset_code_time', 0)
        if datetime.now().timestamp() - code_time > 600:
            session.pop('reset_code', None)
            session.pop('reset_email', None)
            session.pop('reset_code_time', None)
            session.pop('reset_last_sent', None)
            return render_template('reset_password.html', step=1, error="Время истекло. Начните восстановление заново.")

        if not check_password_hash(real_code, input_code):
            return render_template('reset_password.html', step=2, code_error=True, email=email)

        return render_template('reset_password.html', step=3, email=email)

    else:
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            return render_template('reset_password.html', step=3, error="Пароли не совпадают")

        if len(password) < 6:
            return render_template('reset_password.html', step=3, error="Пароль должен быть не менее 6 символов")

        email = session.get('reset_email')
        if not email:
            return redirect('/')

        ses = db_session.create_session()
        user = ses.query(User).filter(User.email == email).first()

        if user:
            user.password = generate_password_hash(password)
            ses.commit()

            session.pop('reset_code', None)
            session.pop('reset_email', None)
            session.pop('reset_code_time', None)
            session.pop('reset_last_sent', None)

            ses.close()
            return redirect('/?reset_success=true')

        ses.close()
        return redirect('/')


@app.route("/resend_reset_code", methods=["POST"])
def resend_reset_code():
    """Повторная отправка кода для восстановления пароля"""
    email = session.get('reset_email')
    if not email:
        return {'error': 'Сессия истекла'}, 400

    last_sent = session.get('reset_last_sent', 0)
    if datetime.now().timestamp() - last_sent < 120:
        remaining = 120 - int(datetime.now().timestamp() - last_sent)
        return {'error': f'Подождите {remaining} секунд перед повторной отправкой'}, 429

    code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    session['reset_code'] = generate_password_hash(code)
    session['reset_code_time'] = datetime.now().timestamp()
    session['reset_last_sent'] = datetime.now().timestamp()

    subject = "Восстановление пароля BinaryClash"
    body = f"Ваш код для восстановления пароля: {code}"

    if send_email(email, subject, body):
        return {'success': True}
    else:
        return {'error': 'Не удалось отправить письмо'}, 500


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


@app.route('/profile/username', methods=['POST'])
@login_required
def change_username():
    new_name = request.form.get('user_name', '').strip()

    if len(new_name) < 3 or len(new_name) > 24:
        return redirect('/profile?status=name_len')

    ses = db_session.create_session()
    taken = ses.query(User).filter(
        User.user_name == new_name,
        User.id != session['user_id']
    ).first()
    if taken:
        ses.close()
        return redirect('/profile?status=name_taken')

    user = ses.query(User).filter(User.id == session['user_id']).first()
    user.user_name = new_name
    ses.commit()
    session['user_name'] = new_name
    ses.close()
    return redirect('/profile?status=name_saved')


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
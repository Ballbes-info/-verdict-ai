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
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY',
                           'dev-secret-cgggggggg   dsfasfasdfasdfasdfasdfsdfsfsdfsdfasdfdfasdfsdfsdfsdfshange-me')
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
            return render_template('register.html', error=None, email_in=1, passw_error=0, step=1)

        passs = request.form.get('pass')
        rep_pass = request.form.get('repid_pass')
        if passs != rep_pass:
            return render_template('register.html', error=None, email_in=0, passw_error=1, step=1)

        if len(passs) < 6:
            return render_template('register.html', error=None, email_in=0, passw_error=1, step=1)

        gmail_user = os.getenv('GMAIL_USERNAME')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        if not gmail_user or not gmail_password:
            app.logger.error("GMAIL_USERNAME / GMAIL_PASSWORD не заданы — письмо не отправлено")
            return render_template('register.html', error=None, email_in=0,
                                   passw_error=0, mail_error=1, step=1)

        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        try:
            msg = EmailMessage()
            msg.set_content(f"Код подтверждения: {code}")
            msg["Subject"] = f"Код подтверждения BinaryClash: {code}"
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

    gmail_user = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')

    try:
        msg = EmailMessage()
        msg.set_content(f"Код подтверждения: {code}")
        msg["Subject"] = "Код подтверждения BinaryClash"
        msg["From"] = gmail_user
        msg["To"] = email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        return {'success': True}
    except:
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

        gmail_user = os.getenv('GMAIL_USERNAME')
        gmail_password = os.getenv('GMAIL_PASSWORD')

        try:
            msg = EmailMessage()
            msg.set_content(f"Код для восстановления пароля: {code}")
            msg["Subject"] = "Восстановление пароля BinaryClash"
            msg["From"] = gmail_user
            msg["To"] = email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.send_message(msg)
        except Exception as e:
            app.logger.error(f"Ошибка отправки письма: {e}")
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

    gmail_user = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')

    try:
        msg = EmailMessage()
        msg.set_content(f"Код для восстановления пароля: {code}")
        msg["Subject"] = "Восстановление пароля BinaryClash"
        msg["From"] = gmail_user
        msg["To"] = email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        return {'success': True}
    except:
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


@app.route('/generate_nickname', methods=['POST'])
@login_required
def generate_nickname():
    with open("nicknames.json", mode='r', encoding='utf-8') as f:
        nicknames_data = json.load(f)

    ses = db_session.create_session()
    while True:
        nick_name = f'{random.choice(nicknames_data)}{random.randint(1, 1000000000)}'
        if not ses.query(User).filter(User.user_name == nick_name).first():
            break

    ses.close()
    return {'nickname': nick_name}


AVATAR_FOLDER = os.path.join('static', 'avatars')


@app.route('/get_avatars')
@login_required
def get_avatars():
    avatars = []
    if os.path.exists(AVATAR_FOLDER):
        for filename in os.listdir(AVATAR_FOLDER):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                avatars.append(f'/static/avatars/{filename}')
    return {'avatars': avatars}


@app.route('/profile/avatar/library', methods=['POST'])
@login_required
def set_avatar_from_library():
    avatar_path = request.form.get('avatar_path')
    if not avatar_path or not avatar_path.startswith('/static/avatars/'):
        return redirect('/profile?status=badavatar')

    ses = db_session.create_session()
    user = ses.query(User).filter(User.id == session['user_id']).first()

    if user:
        try:
            full_path = os.path.join('.', avatar_path.lstrip('/'))
            if os.path.exists(full_path):
                img = Image.open(full_path)
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
                data_uri = f'data:image/jpeg;base64,{encoded}'

                user.avatar = data_uri
                ses.commit()
        except Exception as e:
            app.logger.error(f"Ошибка установки аватара из библиотеки: {e}")

    ses.close()
    return redirect('/profile?status=avatar_saved')


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


COURT_MODELS = [
    # === Groq ===
    {"id": "groq/llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "service": "Groq", "strength": 5,
     "speed": "Мгновенно", "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/openai-gpt-oss-120b", "name": "GPT-OSS 120B", "service": "Groq", "strength": 5, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Затратная"},
    {"id": "groq/qwen-qwen3-32b", "name": "Qwen 3 32B", "service": "Groq", "strength": 4, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/meta-llama-llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "service": "Groq",
     "strength": 4, "speed": "Мгновенно", "speed_cls": "instant", "russian": "mid", "tokens": "Средняя"},
    {"id": "groq/qwen-qwen3.6-27b", "name": "Qwen 3.6 27B", "service": "Groq", "strength": 4, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/llama-3.1-8b-instant", "name": "Llama 3.1 8B", "service": "Groq", "strength": 3, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "mid", "tokens": "Экономная"},
    {"id": "groq/openai-gpt-oss-20b", "name": "GPT-OSS 20B", "service": "Groq", "strength": 3, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},

    # === Mistral ===
    {"id": "mistral/mistral-large-latest", "name": "Mistral Large", "service": "Mistral", "strength": 5,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Затратная"},
    {"id": "mistral/mistral-medium-latest", "name": "Mistral Medium", "service": "Mistral", "strength": 4,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "mistral/mistral-small-latest", "name": "Mistral Small", "service": "Mistral", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Экономная"},
    {"id": "mistral/open-mistral-nemo", "name": "Mistral Nemo", "service": "Mistral", "strength": 3, "speed": "Быстро",
     "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "mistral/ministral-8b-latest", "name": "Ministral 8B", "service": "Mistral", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},
    {"id": "mistral/ministral-3b-latest", "name": "Ministral 3B", "service": "Mistral", "strength": 2,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},

    # === OpenRouter ===
    {"id": "openrouter/nvidia-nemotron-3-ultra-550b-a55b", "name": "Nemotron 3 Ultra", "service": "OpenRouter",
     "strength": 5, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Затратная"},
    {"id": "openrouter/nvidia-nemotron-3-super-120b-a12b", "name": "Nemotron 3 Super", "service": "OpenRouter",
     "strength": 5, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Затратная"},
    {"id": "openrouter/openai-gpt-oss-120b", "name": "GPT-OSS 120B", "service": "OpenRouter", "strength": 5,
     "speed": "Средне", "speed_cls": "mid", "russian": "good", "tokens": "Затратная"},
    {"id": "openrouter/google-gemma-4-26b-a4b-it", "name": "Gemma 4 26B", "service": "OpenRouter", "strength": 4,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Средняя"},
    {"id": "openrouter/nvidia-nemotron-3-nano-30b-a3b", "name": "Nemotron Nano 30B", "service": "OpenRouter",
     "strength": 3, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Экономная"},
    {"id": "openrouter/nvidia-nemotron-nano-9b-v2", "name": "Nemotron Nano 9B", "service": "OpenRouter", "strength": 3,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Средняя"},
    {"id": "openrouter/cohere-north-mini-code", "name": "North Mini Code", "service": "OpenRouter", "strength": 3,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Экономная"},

    # === GitHub ===
    {"id": "github/gpt-4o", "name": "GPT-4o", "service": "GitHub", "strength": 5, "speed": "Средне", "speed_cls": "mid",
     "russian": "good", "tokens": "Средняя"},
    {"id": "github/gpt-4o-mini", "name": "GPT-4o mini", "service": "GitHub", "strength": 5, "speed": "Средне",
     "speed_cls": "mid", "russian": "good", "tokens": "Экономная"},

    # === Cerebras ===
    {"id": "cerebras/gpt-oss-120b", "name": "GPT-OSS 120B", "service": "Cerebras", "strength": 5, "speed": "Быстро",
     "speed_cls": "fast", "russian": "good", "tokens": "Затратная"},
    {"id": "cerebras/gemma-4-31b", "name": "Gemma 4 31B", "service": "Cerebras", "strength": 4, "speed": "Быстро",
     "speed_cls": "fast", "russian": "mid", "tokens": "Средняя"},

    # === Cloudflare ===
    {"id": "cloudflare/deepseek-r1-distill-qwen-32b", "name": "DeepSeek R1 32B", "service": "Cloudflare", "strength": 4,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "cloudflare/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "service": "Cloudflare", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},

    # === GigaChat ===
    {"id": "gigachat/gigachat", "name": "GigaChat (Сбер)", "service": "GigaChat", "strength": 3, "speed": "Средне",
     "speed_cls": "mid", "russian": "native", "tokens": "Средняя"},

    # === Gemini ===
    {"id": "gemini/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "service": "Gemini", "strength": 3, "speed": "Средне",
     "speed_cls": "mid", "russian": "good", "tokens": "Экономная"},
]

CLASSIC_COURT_ROLES = [
    {"key": "prosecutor", "name": "Прокурор", "accent": "red",
     "desc": "Обвинение. Требует доказать вину и добивается сурового приговора."},
    {"key": "advocate", "name": "Адвокат", "accent": "blue",
     "desc": "Защита. Ищет слабости обвинения и отстаивает подсудимого."},
    {"key": "judge", "name": "Судья", "accent": "gold",
     "desc": "Беспристрастный арбитр. Анализирует спор и выносит вердикт."},
]

PROMPT_VERSIONS = [
    {"key": "FULL", "name": "FULL — Максимальное качество", "tokens": "1500-4000", "icon": "⭐", "desc": "Детальные аргументы, глубокий анализ"},
    {"key": "MEDIUM", "name": "MEDIUM — Оптимальный баланс", "tokens": "400-1000", "icon": "⚖️", "desc": "Хорошее качество, экономия токенов"},
    {"key": "COMPACT", "name": "COMPACT — Быстро и дёшево", "tokens": "100-400", "icon": "⚡", "desc": "Быстрые игры, минимальные затраты"},
]

@app.route('/classic_court/select_model', methods=["GET", "POST"])
@login_required
def select_models():
    if request.method == "POST":
        session['classic_court'] = {
            'prosecutor': request.form.get('prosecutor'),
            'advocate': request.form.get('advocate'),
            'judge': request.form.get('judge'),
        }
        return redirect('/classic_court/select_prompt_version')
    return render_template('select_models.html', models=COURT_MODELS, roles=CLASSIC_COURT_ROLES)


@app.route('/classic_court/select_prompt_version', methods=["GET", "POST"])
@login_required
def select_prompt_version():
    if request.method == "POST":
        # Сохраняем версию промпта
        session['classic_court']['prompt_version'] = request.form.get('prompt_version')
        # Сохраняем характеры (пока заглушка)
        session['classic_court']['personalities'] = {
            'prosecutor': request.form.get('prosecutor_personality', 'default'),
            'advocate': request.form.get('advocate_personality', 'default'),
            'judge': request.form.get('judge_personality', 'default'),
        }
        return redirect('/classic_court/select_topic')

    return render_template(
        'select_prompt_version.html',
        versions=PROMPT_VERSIONS,
        roles=CLASSIC_COURT_ROLES
    )

if __name__ == "__main__":
    app.run(debug=True)
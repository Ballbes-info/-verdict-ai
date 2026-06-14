from flask import Flask, render_template, request
from data.user import User
import json
import random
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

db_session.global_init('db/blogs.db')


@app.route("/", methods=["POST", "GET"])
def welcome():
    
    if request.method == "POST":
        ses = db_session.create_session()
        email = request.form.get('email', '').strip()
        check_email = ses.query(User).filter(User.email == email).first()
        
        if check_email:
            passw = check_email.password
            check_password = check_password_hash(passw, request.form.get('password'))
            if check_password:
                return "56"
        


    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    email = request.args.get("email", "")
    password = request.args.get("password", "")
    return render_template("login.html", email=email, password=password)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template('register.html', error=None)
    elif request.method == "POST":
        email = request.form.get('email', '').strip()
        ses = db_session.create_session()
        user = ses.query(User).filter(User.email == email).first()
        if not user:
            while True:
                with open("nicknames.json", mode='r', encoding='utf-8') as f:
                    data = json.load(f)
                random_word  = random.choice(data)
                random_number = random.randint(1, 1000000000)
                nick_name = f'{random_word}{random_number}'
                nick = ses.query(User).filter(User.user_name == nick_name).first()
                if not nick:
                    break
            
            new_user = User()
            new_user.email = email
            new_user.password = generate_password_hash(request.form.get('pass'))
            new_user.user_name = nick_name
            ses.add(new_user)
            ses.commit()
            ses.close()
            return "56"


        


@app.route("/court")
def court():
    return render_template("court.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route('/select_mode')
def select_mode():
    return render_template('modes.html')

if __name__ == "__main__":
    app.run(debug=True)

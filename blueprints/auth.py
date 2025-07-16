# 用于授权
from flask import Blueprint, render_template, jsonify, redirect, url_for, session, flash
from exts import mail, db
from flask_mail import Message
from flask import request
import string, random
from models import EmailCaptchaModel, UserModel
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError

bp = Blueprint("spirit", __name__, url_prefix="/spirit")

@bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        form = LoginForm(request.form)
        if form.validate():
            email = form.email.data
            password = form.password.data
            user = UserModel.query.filter_by(email=email).first()
            if not user:
                flash("This email address has not been registered!", "danger")
                return redirect(url_for("spirit.login"))
            if check_password_hash(user.password, password):
                session["user_id"] = user.id
                return redirect("/Spirit/Homepage")
            else:
                flash("The account or password is incorrect, please try again!", "danger")
                return redirect(url_for("spirit.login"))
        else:
            flash("The account or password is incorrect, please try again!", "danger")
            return redirect(url_for("spirit.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    form = RegisterForm(request.form)
    if form.validate():
        try:
            user = UserModel(
                email=form.email.data,
                username=form.username.data,
                password=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration is successful, please log in!", "success")
            return redirect(url_for("spirit.login"))
        except IntegrityError:
            db.session.rollback()
            flash("An email address or username has already been registered.", "danger")
            return redirect(url_for("spirit.register"))
    flash("Form validation failed!", "danger")
    return redirect(url_for("spirit.register"))


@bp.route("/captcha/email")
def get_email_captcha():
    email = request.args.get('email')
    name = request.args.get('name')
    if name is None:
        name = "user"
    source = (string.digits + string.ascii_letters) * 6
    captcha = "".join(random.sample(source, 6))

    if email:
        EmailCaptchaModel.query.filter_by(email=email).delete()

        message = Message(subject="Spirit register Captcha: ", recipients=[email],
                          body=f"Hello, {name}!\n\n"
                               f"Welcome to Spirit Todo!\n\n"
                               f"Thanks for registering for an account, you can enter this code to it: \n\n\n"
                               f"{captcha}\n\n\n"
                               f"If you weren't trying to register in, then you don't need to take any action.\n\n")
        mail.send(message)
        email_captcha = EmailCaptchaModel(email=email, captcha=captcha)
        db.session.add(email_captcha)
        db.session.commit()
    return jsonify({"code": 200, "message": "", "data": None})

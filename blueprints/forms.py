import wtforms
from wtforms.validators import Email, Length, EqualTo, InputRequired
from models import UserModel, EmailCaptchaModel
from exts import db


# 表单验证
class RegisterForm(wtforms.Form):
    email = wtforms.StringField(validators=[Email(message="Please enter a valid email address!")])
    captcha = wtforms.StringField(validators=[Length(min=6, max=6, message="The captcha code is formatted incorrectly!")])
    username = wtforms.StringField(validators=[Length(min=2, max=20, message="The username is formatted incorrectly!")])
    password = wtforms.PasswordField(validators=[Length(min=8, max=20, message="The length of the password is 8 ~ 20 digits!")])
    password_confirm = wtforms.PasswordField(validators=[EqualTo("password", message="The password must match!")])

    # 验证邮箱是否注册
    def validate_email(self, field):
        email =field.data
        user = UserModel.query.filter_by(email=email).first()
        if user:
            raise wtforms.ValidationError("Email already registered.")

    # 验证验证码是否正常
    def validate_captcha(self, field):
        captcha = field.data
        email = self.email.data
        captcha_model = EmailCaptchaModel.query.filter_by(email=email, captcha=captcha).first()
        if not captcha_model:
            raise wtforms.ValidationError("Captcha already used.")


class LoginForm(wtforms.Form):
    email = wtforms.StringField(validators=[Email(message="Please enter a valid email address!")])
    password =wtforms.StringField(validators=[Length(min=8, max=20, message="The length of the password is 8 ~ 20 digits")])


class TodoForm(wtforms.Form):
    title = wtforms.StringField(validators=[Length(min=2, max=100, message="The title is formatted incorrectly!")])
    brief = wtforms.StringField(validators=[Length(min=0, max=200, message="The brief was overflow!")])
    content = wtforms.TextAreaField(validators=[Length(max=2000, message="The content is too long!")])
    deadline = wtforms.StringField(validators=[wtforms.validators.DataRequired(message="The todo deadline is required!")])
    start_time = wtforms.StringField()
    completed_time = wtforms.StringField()

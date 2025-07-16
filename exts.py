# 扩展文件, 解决循环调用
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


db = SQLAlchemy()

mail = Mail()
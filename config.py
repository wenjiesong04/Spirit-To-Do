from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件

# 安全配置
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret')
# # 数据库配置信息
# HOSTNAME = "127.0.0.1"
# # MySQL监听端口号
# PORT = "3306"
# # 连接MySQL的用户名
# USERNAME = "root"
# PASSWORD = "25802580"
# # 数据库名称
# DATABASE = "spirit"

# SQLite 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
SQLALCHEMY_TRACK_MODIFICATIONS = True

# 邮箱配置
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "true").lower() == "true"
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
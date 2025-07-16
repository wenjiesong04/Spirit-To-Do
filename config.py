SECRET_KEY = "SpiritisabestTodosoftware!"

# # 数据库配置信息
# HOSTNAME = "127.0.0.1"
# # MySQL监听端口号
# PORT = "3306"
# # 连接MySQL的用户名
# USERNAME = "root"
# PASSWORD = "25802580"
# # 数据库名称
# DATABASE = "spirit"
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
SQLALCHEMY_TRACK_MODIFICATIONS = True


# 邮箱配置
MAIL_SERVER = "smtp.qq.com"
MAIL_USE_SSL = True
MAIL_PORT = 465
MAIL_USERNAME = "3518648435@qq.com"
MAIL_PASSWORD = "coqnhwyrtqzdciei"
MAIL_DEFAULT_SENDER = "3518648435@qq.com"
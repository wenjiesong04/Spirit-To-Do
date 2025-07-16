from datetime import datetime
from flask import Flask, session, g, redirect, url_for, jsonify
import config
from exts import db, mail
from models import UserModel
from blueprints.auth import bp as auth_bp
from blueprints.todo import bp as sh_bp
from blueprints.friend_functions.friend import bp as friend_bp
from blueprints.todo_content import bp as todo_content_bp
from blueprints.in_box import bp as inbox_bp
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
import os


app = Flask(__name__)
# 绑定配置
app.config.from_object(config)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret')
app.config["SCHEDULER_API_ENABLED"] = True
# 传入app.py
db.init_app(app)
mail.init_app(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

migrate = Migrate(app, db)

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(sh_bp)
app.register_blueprint(friend_bp)
app.register_blueprint(todo_content_bp)
app.register_blueprint(inbox_bp)

# 自定义错误处理程序，确保返回JSON
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    import traceback
    traceback.print_exc()
    return jsonify({"error": "Internal server error"}), 500

def priority_label(priority):
    mapping = {
        0: "Pending",
        1: "Normal",
        2: "Important",
        3: "Urgent"
    }
    return mapping.get(priority, "Unknown")

def priority_color(priority):
    mapping = {
        0: "secondary",
        1: "primary",
        2: "warning",
        3: "danger"
    }
    return mapping.get(priority, "secondary")

# 注册过滤器
app.jinja_env.filters['priority_label'] = priority_label
app.jinja_env.filters['priority_color'] = priority_color

@app.route('/')
def hello_world():
    return redirect(url_for("spirit.login"))

@app.before_request
def spirit_before_request():
    user_id = session.get('user_id')
    if user_id:
        user = UserModel.query.get(user_id)
        # 绑定用户信息在一个对象上
        setattr(g, 'user', user)
    else:
        # 避免g的user对象找不到
        setattr(g, 'user', None)


# 上下文处理器
@app.context_processor
def spirit_context_processor():
    user = getattr(g, 'user', None)
    user_id = user.id if user else None
    username = user.username if user else None
    now_time = datetime.now()
    return {"user": user, "user_id": user_id, "username": username, "now_time": now_time}

from tasks import register_tasks

register_tasks(scheduler)

if __name__ == '__main__':
    app.run()


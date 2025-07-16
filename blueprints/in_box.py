from datetime import datetime
import pytz
from datetime import timedelta
from flask import Blueprint, render_template, session, redirect, url_for, flash, g, jsonify
from blueprints.forms import TodoForm
from exts import db
from flask import request
from models import UserModel, TodoModel, UserTodoModel
from models import FriendModel, ProjectCollaboratorModel, FriendGroupModel
from models import NotificationModel
from pyecharts.charts import Calendar
from pyecharts import options as opts
from sqlalchemy import func, or_
from datetime import date, timedelta

bp = Blueprint("in_box", __name__, url_prefix="/Spirit/In-Box")
from flask import request


# =================== Notification APIs ===================

@bp.route("/api/notifications", methods=["GET"])
def get_notifications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"code": 401, "msg": "Unauthorized"}), 401

    notifications = NotificationModel.query.filter_by(user_id=user_id).order_by(NotificationModel.created_time.desc()).all()
    data = [
        {
            "id": n.id,
            "content": n.content,
            "created_time": n.created_time.strftime("%Y-%m-%d %H:%M"),
            "is_read": n.is_read
        }
        for n in notifications
    ]
    return jsonify({"notifications": data})


@bp.route("/api/notifications/clear", methods=["POST"])
def clear_notifications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"code": 401, "msg": "Unauthorized"}), 401

    NotificationModel.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"code": 200, "msg": "Cleared"})


@bp.route("/notifications", methods=["GET"])
def notifications():
    return render_template("inbox.html")

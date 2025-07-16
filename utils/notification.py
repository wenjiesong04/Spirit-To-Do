from models import NotificationModel
from exts import db
from datetime import datetime

def add_notification(user_id, content):
    today = datetime.now().date()
    exists = NotificationModel.query.filter(
        NotificationModel.user_id == user_id,
        NotificationModel.content == content,
        NotificationModel.created_time >= datetime(today.year, today.month, today.day)
    ).first()
    if exists:
        return  # 已有同样内容的通知，今天不再写入
    notification = NotificationModel(
        user_id=user_id,
        content=content
    )
    db.session.add(notification)
    db.session.commit() 
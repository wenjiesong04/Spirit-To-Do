from exts import db
from datetime import datetime


class UserModel(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    join_time = db.Column(db.DateTime, default=datetime.now)
    photo = db.Column(db.String(255))

    todos = db.relationship('UserTodoModel', back_populates='user', cascade='all, delete-orphan')


class TodoModel(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    brief = db.Column(db.String(200))
    content = db.Column(db.TEXT)
    date = db.Column(db.DateTime, default=datetime.now)
    start_time = db.Column(db.DateTime, nullable=True,default=datetime.now)
    deadline = db.Column(db.DateTime, nullable=False)
    completed_time = db.Column(db.DateTime, nullable=True)
    # 0: 未开始, 1: 进行中, 2: 已完成, 3: 逾期未完成
    status = db.Column(db.Integer, default=1)
    # 0: 暂缓, 1: 一般, 2: 加急, 3: 暴肝
    priority = db.Column(db.Integer, default=1)
    mail_notify = db.Column(db.Boolean, default=False)

    is_deleted = db.Column(db.Boolean, default=False)
    deleted_time = db.Column(db.DateTime)

    users = db.relationship("UserTodoModel", back_populates="todo", cascade="all, delete-orphan")


class UserTodoModel(db.Model):
    __tablename__ = 'user_todos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todos.id'), nullable=False)

    user = db.relationship("UserModel", back_populates="todos")
    todo = db.relationship("TodoModel", back_populates="users")


class EmailCaptchaModel(db.Model):
    __tablename__ = 'captcha'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False)
    captcha = db.Column(db.String(100), nullable=False)


class FriendGroupModel(db.Model):
    __tablename__ = 'friend_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_name = db.Column(db.String(64), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('UserModel', backref='friend_groups')


class FriendModel(db.Model):
    __tablename__ = 'friends'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('friend_groups.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('UserModel', foreign_keys=[user_id], backref='friends')
    friend = db.relationship('UserModel', foreign_keys=[friend_id])
    group = db.relationship('FriendGroupModel', backref='friends')


class ProjectCollaboratorModel(db.Model):
    __tablename__ = 'project_collaborators'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todos.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permission = db.Column(db.Enum('view', 'edit', name='collab_permission'), default='view')
    active = db.Column(db.Boolean, default=True)  # 是否仍为有效协作者
    added_at = db.Column(db.DateTime, default=datetime.now)

    todo = db.relationship('TodoModel', backref='collaborators')
    user = db.relationship('UserModel', backref='collaborations')


class NotificationModel(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(256), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
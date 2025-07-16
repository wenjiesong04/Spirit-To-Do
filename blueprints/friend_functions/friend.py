from flask import Blueprint, request, jsonify, g, redirect, url_for
from exts import db
from models import UserModel, FriendModel
from models import FriendGroupModel
from sqlalchemy import or_

bp = Blueprint("friend", __name__, url_prefix="/friend")


@bp.route("/add", methods=["POST"])
def add_friend():
    if request.is_json:
        data = request.get_json()
        identifier = data.get("identifier")  # username, email, or user ID
        group_name = data.get("group_name")
    else:
        identifier = request.form.get("friend_query")
        group_name = request.form.get("group_name")

    current_user_id = g.user.id

    # 查找好友
    friend_user = (
        UserModel.query.filter(
            (UserModel.username == identifier) |
            (UserModel.email == identifier) |
            (UserModel.id == identifier)
        ).first()
    )

    if not friend_user:
        if request.is_json:
            return jsonify({"error": "User not found."}), 404
        else:
            return redirect(url_for("Spirit.home"))  # 或者渲染带错误提示的页面

    if friend_user.id == current_user_id:
        if request.is_json:
            return jsonify({"error": "Cannot add yourself as a friend."}), 400
        else:
            return redirect(url_for("Spirit.home"))

    # 已是好友则不重复添加
    exists = FriendModel.query.filter_by(user_id=current_user_id, friend_id=friend_user.id).first()
    if exists:
        if request.is_json:
            return jsonify({"error": "Already friends."}), 400
        else:
            return redirect(url_for("Spirit.home"))

    # 获取或创建分组
    if group_name:
        group = FriendGroupModel.query.filter_by(user_id=current_user_id, group_name=group_name).first()
        if not group:
            group = FriendGroupModel(user_id=current_user_id, group_name=group_name)
            db.session.add(group)
            db.session.flush()
    else:
        group = FriendGroupModel.query.filter_by(user_id=current_user_id, group_name="Default group").first()
        if not group:
            group = FriendGroupModel(user_id=current_user_id, group_name="Default group", is_default=True)
            db.session.add(group)
            db.session.flush()

    # 添加好友：双向关系
    relation1 = FriendModel(user_id=current_user_id, friend_id=friend_user.id, group_id=group.id)
    relation2 = FriendModel(user_id=friend_user.id, friend_id=current_user_id)

    db.session.add_all([relation1, relation2])
    db.session.commit()

    if request.is_json:
        return jsonify({"message": "Friend added successfully."}), 200
    else:
        return redirect(url_for("Spirit.home"))


@bp.route("/list", methods=["GET"])
def list_friends():
    current_user_id = g.user.id

    # 获取所有好友分组及好友信息
    groups = FriendGroupModel.query.filter_by(user_id=current_user_id).all()
    result = []

    # 先处理有分组的好友
    for group in groups:
        friends = FriendModel.query.filter_by(user_id=current_user_id, group_id=group.id).all()
        friend_data = []
        for f in friends:
            user = UserModel.query.get(f.friend_id)
            friend_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "group": group.group_name
            })
        result.append({
            "group": group.group_name,
            "friends": friend_data
        })

    # 处理未分组（group_id is None）的好友，命名为“Default group”
    ungrouped_friends = FriendModel.query.filter_by(user_id=current_user_id, group_id=None).all()
    if ungrouped_friends:
        friend_data = []
        for f in ungrouped_friends:
            user = UserModel.query.get(f.friend_id)
            friend_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "group": "Default group"
            })
        result.append({
            "group": "Default group",
            "friends": friend_data
        })

    return jsonify(result)


@bp.route("/delete/<int:friend_id>", methods=["POST"])
def delete_friend(friend_id):
    current_user_id = g.user.id

    # 删除双向好友关系
    FriendModel.query.filter(
        or_(
            (FriendModel.user_id == current_user_id) & (FriendModel.friend_id == friend_id),
            (FriendModel.user_id == friend_id) & (FriendModel.friend_id == current_user_id)
        )
    ).delete(synchronize_session=False)

    db.session.commit()
    # Only redirect for non-JSON requests (e.g. browser POSTs)
    if not request.is_json:
        return redirect(url_for("Spirit.home"))
    return jsonify({"message": "Friend deleted successfully."}), 200


@bp.route("/move_group", methods=["POST"])
def move_friend_group():
    data = request.json
    friend_id = data.get("friend_id")
    new_group_id = data.get("group_id")
    current_user_id = g.user.id

    relation = FriendModel.query.filter_by(user_id=current_user_id, friend_id=friend_id).first()
    if not relation:
        return jsonify({"error": "Friend relationship not found."}), 404

    relation.group_id = new_group_id
    db.session.commit()
    # Only redirect for non-JSON requests (e.g. browser POSTs)
    if not request.is_json:
        return redirect(url_for("Spirit.home"))
    return jsonify({"message": "Friend moved to new group successfully."}), 200


# 新增分组列表接口
@bp.route("/groups", methods=["GET"])
def get_groups():
    current_user_id = g.user.id
    groups = FriendGroupModel.query.filter_by(user_id=current_user_id).all()
    return jsonify([
        {"id": g.id, "name": g.group_name}
        for g in groups
    ])
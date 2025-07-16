from flask import Blueprint, request, jsonify, g
from exts import db
from models import FriendGroupModel, FriendModel

bp = Blueprint("group", __name__, url_prefix="/group")


@bp.route("/create", methods=["POST"])
def create_group():
    data = request.json
    group_name = data.get("group_name")
    current_user_id = g.user.id

    if not group_name:
        return jsonify({"error": "Group name required."}), 400

    group = FriendGroupModel(user_id=current_user_id, group_name=group_name, is_default=False)
    db.session.add(group)
    db.session.commit()

    return jsonify({"message": "Group created successfully.", "group_id": group.id})


@bp.route("/rename/<int:group_id>", methods=["POST"])
def rename_group(group_id):
    data = request.json
    new_name = data.get("group_name")
    current_user_id = g.user.id

    group = FriendGroupModel.query.filter_by(id=group_id, user_id=current_user_id).first()
    if not group:
        return jsonify({"error": "Group not found."}), 404

    group.group_name = new_name
    db.session.commit()
    return jsonify({"message": "Group renamed."})


@bp.route("/delete/<int:group_id>", methods=["POST"])
def delete_group(group_id):
    current_user_id = g.user.id

    group = FriendGroupModel.query.filter_by(id=group_id, user_id=current_user_id).first()
    if not group:
        return jsonify({"error": "Group not found."}), 404

    if group.is_default:
        return jsonify({"error": "Cannot delete default group."}), 400

    # 将所属该组的好友 group_id 设为 null（或默认组）
    FriendModel.query.filter_by(group_id=group_id).update({FriendModel.group_id: None})
    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Group deleted."})
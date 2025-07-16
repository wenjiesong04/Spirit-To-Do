from flask import Blueprint, request, jsonify, g
from exts import db
from models import ProjectCollaboratorModel, TodoModel, UserModel

bp = Blueprint("collab", __name__, url_prefix="/collab")


@bp.route("/add", methods=["POST"])
def add_collaborator():
    data = request.json
    todo_id = data.get("todo_id")
    user_id = data.get("user_id")  # 协作者ID
    permission = data.get("permission", "view")

    # 检查是否存在重复协作
    exists = ProjectCollaboratorModel.query.filter_by(todo_id=todo_id, user_id=user_id).first()
    if exists and exists.active:
        return jsonify({"error": "User is already a collaborator."}), 400

    if exists:
        exists.permission = permission
        exists.active = True
    else:
        collab = ProjectCollaboratorModel(todo_id=todo_id, user_id=user_id, permission=permission)
        db.session.add(collab)

    db.session.commit()
    return jsonify({"message": "Collaborator added."})


@bp.route("/set_permission", methods=["POST"])
def set_permission():
    data = request.json
    todo_id = data.get("todo_id")
    user_id = data.get("user_id")
    permission = data.get("permission")  # "view" or "edit"

    collab = ProjectCollaboratorModel.query.filter_by(todo_id=todo_id, user_id=user_id, active=True).first()
    if not collab:
        return jsonify({"error": "Collaborator not found."}), 404

    collab.permission = permission
    db.session.commit()
    return jsonify({"message": "Permission updated."})


@bp.route("/remove", methods=["POST"])
def remove_collaborator():
    data = request.json
    todo_id = data.get("todo_id")
    user_id = data.get("user_id")

    collab = ProjectCollaboratorModel.query.filter_by(todo_id=todo_id, user_id=user_id).first()
    if not collab:
        return jsonify({"error": "Collaborator not found."}), 404

    collab.active = False
    db.session.commit()
    return jsonify({"message": "Collaborator removed."})


# Add revoke_access_form route for revoking all collaborations for a user
@bp.route("/revoke_access", methods=["POST"], endpoint="revoke_access_form")
def revoke_access_form():
    friend_id = request.form.get("friend_id")
    if not friend_id:
        return jsonify({"error": "Missing friend_id"}), 400

    collaborations = ProjectCollaboratorModel.query.filter_by(user_id=friend_id, active=True).all()
    for collab in collaborations:
        collab.active = False

    db.session.commit()
    return jsonify({"message": "Access revoked."})
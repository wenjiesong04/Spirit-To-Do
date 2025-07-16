from functools import wraps
from flask import abort, g
from models import UserTodoModel, ProjectCollaboratorModel


def require_todo_permission(required='view'):
    """
    装饰器：检查当前用户是否拥有某个 todo 项目的访问权限或编辑权限。
    用法：@require_todo_permission('edit')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(todo_id, *args, **kwargs):
            user = g.user
            if not user:
                # 未登录
                abort(401)

            # 检查是否是 owner
            is_owner = UserTodoModel.query.filter_by(
                user_id=user.id, todo_id=todo_id
            ).first() is not None

            if is_owner:
                return func(todo_id, *args, **kwargs)

            # 检查是否为协作者
            collab = ProjectCollaboratorModel.query.filter_by(
                todo_id=todo_id, user_id=user.id, active=True
            ).first()

            if not collab:
                # 没有权限，拒绝访问
                abort(403)

            # 检查协作者是否有edit权限
            if required == 'edit' and collab.permission != 'edit':
                abort(403)

            return func(todo_id, *args, **kwargs)

        return wrapper
    return decorator

from datetime import datetime
from datetime import timedelta
from datetime import date
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, make_response, current_app
from blueprints.forms import TodoForm
from exts import db
from flask import request
from models import UserModel, TodoModel, UserTodoModel
from models import FriendModel, ProjectCollaboratorModel, FriendGroupModel
from utils.notification import add_notification

bp = Blueprint("Spirit", __name__, url_prefix="/Spirit")

@bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("spirit.login")))
    session.clear()
    session.permanent = False

    # 显式地设置session cookie的过期时间为过去
    response.set_cookie(current_app.config["SESSION_COOKIE_NAME"], '', expires=0)
    # 或者更通用的方法 (如果session_cookie_name未配置，但通常默认为'session')
    # response.set_cookie('session', '', expires=0, path='/') # 确保path匹配

    flash("You have successfully logged out.", "success")
    return response

@bp.route("/Homepage", methods=["GET"])
def home():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("spirit.login"))

    user = UserModel.query.get(user_id)
    # 修改为只获取未被软删除的任务
    todos = db.session.query(TodoModel).join(UserTodoModel).filter(
        UserTodoModel.user_id == user_id,
        TodoModel.is_deleted == False
    ).all()

    now = datetime.now()
    this_year_start = now.replace(month=1, day=1).date()
    this_year_end = now.replace(month=12, day=31).date()

    def is_today_task(todo):
        if not (todo.start_time and todo.deadline):
            return False
        return (todo.start_time.date() <= now.date() <= todo.deadline.date())

    def is_yesterday_task(todo):
        if not (todo.start_time and todo.deadline):
            return False
        yesterday = now.date() - timedelta(days=1)
        return (todo.start_time.date() <= yesterday <= todo.deadline.date())

    def is_this_week_task(todo):
        if not (todo.start_time and todo.deadline):
            return False
        start_of_week = now.date() - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return (todo.start_time.date() <= end_of_week and todo.deadline.date() >= start_of_week)

    def is_this_month_task(todo):
        if not (todo.start_time and todo.deadline):
            return False
        start_of_month = now.replace(day=1).date()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        end_of_month = (next_month - timedelta(days=1)).date()
        return (todo.start_time.date() <= end_of_month and todo.deadline.date() >= start_of_month)

    def is_this_year_task(todo):
        if not (todo.start_time and todo.deadline):
            return False
        return not (todo.deadline.date() < this_year_start or todo.start_time.date() > this_year_end)

    def is_completed(todo):
        return todo.completed_time is not None and todo.completed_time <= now

    def compute_priority(todo):
        # 优先判断 start_time
        if todo.start_time and now < todo.start_time:
            return 0

        # 逾期 1 天内
        if todo.deadline and (todo.deadline - now) < timedelta(days=1):
            return 3

        # 重要
        if getattr(todo, 'important', False):
            return 2

        # 状态 0
        if todo.status == 0:
            return 0  # Preparation（绿色）

        # 一般
        return 1

    for todo in todos:
        todo.priority = compute_priority(todo)
        todo.is_today_task = is_today_task(todo)
        todo.is_yesterday_task = is_yesterday_task(todo)
        todo.is_this_week_task = is_this_week_task(todo)
        todo.is_this_month_task = is_this_month_task(todo)
        todo.is_this_year_task = is_this_year_task(todo)
        todo.is_completed = is_completed(todo)

    for todo in todos:
        # 自动切换未开始到进行中
        if todo.status == 0 and todo.start_time and now >= todo.start_time:
            todo.status = 1
        # 逾期处理
        if todo.status in [0, 1] and todo.deadline and todo.deadline < now:
            todo.status = 3

    db.session.commit()

    # 查询好友分组结构
    friends = FriendModel.query.filter_by(user_id=user_id).all()
    grouped_friends = {}

    for f in friends:
        friend_user = UserModel.query.get(f.friend_id)

        # 获取分组名
        group_obj = FriendGroupModel.query.get(f.group_id)
        group_name = group_obj.group_name if group_obj else 'Default Group'

        # 获取该好友参与的项目（基于 ProjectCollaboratorModel）
        collabs = ProjectCollaboratorModel.query.filter_by(user_id=f.friend_id).all()
        todo_ids = [c.todo_id for c in collabs]

        todo_titles = []
        if todo_ids:
            todo_titles = [t.title for t in TodoModel.query.filter(TodoModel.id.in_(todo_ids)).all()]

        grouped_friends.setdefault(group_name, []).append({
            'id': f.friend_id,
            'username': friend_user.username,
            'projects': todo_titles
        })

    # 构造 dashboard_todos 字典，便于前端 JS 使用
    dashboard_todos = {}
    for todo in todos:
        dashboard_todos[todo.id] = {
            "title": todo.title,
            "brief": todo.brief if hasattr(todo, 'brief') else (todo.content[:30] + "..." if todo.content and len(todo.content) > 30 else todo.content),
            "content": todo.content,
            "start_time": todo.start_time.strftime("%Y-%m-%d %H:%M") if todo.start_time else "",
            "deadline": todo.deadline.strftime("%Y-%m-%d %H:%M") if todo.deadline else "",
            "completed_time": todo.completed_time.strftime("%Y-%m-%d %H:%M") if todo.completed_time else "",
            "status": todo.status,
            "priority": todo.priority,
        }

    return render_template("home.html", todo_list=todos, user=user, grouped_friends=grouped_friends, dashboard_todos=dashboard_todos)

@bp.route("/new_project", methods=["POST"])
def new_project():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 修改为从 request.json 获取数据
    data = request.json
    form = TodoForm(data=data)

    if form.validate():
        # 如果通过验证，处理数据
        start_time_raw = data.get("start_time", "").strip()
        start_time = None
        if start_time_raw:
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
                try:
                    start_time = datetime.strptime(start_time_raw, fmt)
                    break
                except ValueError:
                    continue
            if not start_time:
                return jsonify({"error": "Start time format is incorrect!"}), 400

        completed_time_raw = data.get("completed_time", "").strip()
        completed_time = None
        if completed_time_raw:
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
                try:
                    completed_time = datetime.strptime(completed_time_raw, fmt)
                    break
                except ValueError:
                    continue
            if not completed_time:
                return jsonify({"error": "Completion time format is incorrect!"}), 400

        deadline_raw = data.get("deadline", "").strip()
        deadline = None
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
            try:
                deadline = datetime.strptime(deadline_raw, fmt)
                break
            except ValueError:
                continue
        if not deadline:
            return jsonify({"error": "Deadline format is incorrect!"}), 400

        mail_notify = data.get("mail_notifier", False)

        # ------ 新增：自动判定 status/priority/important ------
        important_checked = data.get("important", False)
        now = datetime.now()
        # 默认一般任务
        status = 1
        priority = 1

        # 已完成
        if completed_time:
            status = 2
        # 未到开始时间
        elif start_time and now < start_time:
            status = 0
            priority = 2 if important_checked else 0
        # 重要任务（未勾选 completed，但勾选重要）
        elif important_checked:
            status = 1
            priority = 2
        # 普通任务（默认即可）

        new_todo = TodoModel(
            title=form.title.data,
            brief=form.brief.data,
            content=form.content.data,
            deadline=deadline,
            status=status,
            completed_time=completed_time,
            start_time=start_time,
            mail_notify=mail_notify,
        )
        db.session.add(new_todo)
        db.session.commit()

        link = UserTodoModel(user_id=user_id, todo_id=new_todo.id)
        db.session.add(link)
        db.session.commit()

        # 添加通知
        add_notification(user_id, f"Add a new todo: {form.title.data}")
        return jsonify({"success": True, "message": "Project created successfully!"})
    else:
        errors = {field: errors for field, errors in form.errors.items()}
        return jsonify({"error": "Form validation failed", "details": errors}), 400


@bp.route("/complete_todo/<int:todo_id>", methods=["POST"])
def complete_todo(todo_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    todo = TodoModel.query.get(todo_id)
    if not todo:
        return jsonify({"error": "Task not found!"}), 404

    # 检查权限
    user_todo_link = UserTodoModel.query.filter_by(user_id=user_id, todo_id=todo_id).first()
    if not user_todo_link:
        return jsonify({"error": "No permission to operate this task"}), 403

    todo.status = 2  # 设置为"已完成"
    todo.completed_time = datetime.now()  # 当前时间
    db.session.commit()

    return jsonify({"success": True, "message": "Task marked as completed!"})


@bp.route("/get_added_blocks", methods=["GET"])
def get_added_blocks():
    added_blocks = session.get("added_blocks", [])
    return jsonify({"added_blocks": added_blocks})


@bp.route("/add_block", methods=["POST"])
def add_block():
    block_name = request.json.get("block_name")
    if not block_name:
        return jsonify({"success": False, "error": "Missing block name"}), 400

    added_blocks = session.get("added_blocks", [])
    if block_name not in added_blocks:
        added_blocks.append(block_name)
        session["added_blocks"] = added_blocks

    return jsonify({"success": True, "added_blocks": added_blocks})

@bp.route("/Project/api/edit", methods=["POST"])
def edit_project():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    todo_id = data.get("id")
    if not todo_id:
        return jsonify({"error": "Missing ID"}), 400

    todo = TodoModel.query.get(todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    # 检查权限
    user_todo_link = UserTodoModel.query.filter_by(user_id=user_id, todo_id=todo_id).first()
    if not user_todo_link:
        return jsonify({"error": "No permission to operate this task"}), 403

    todo.title = data.get("title", todo.title)
    todo.brief = data.get("brief", todo.brief)
    todo.content = data.get("content", todo.content)

    try:
        if data.get("start_time"):
            todo.start_time = datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M")
        elif data.get("start_time") is not None:
            todo.start_time = None

        if data.get("deadline"):
            todo.deadline = datetime.strptime(data["deadline"], "%Y-%m-%dT%H:%M")
        elif data.get("deadline") is not None:
            todo.deadline = None

        if data.get("completed_time"):
            todo.completed_time = datetime.strptime(data["completed_time"], "%Y-%m-%dT%H:%M")
        elif data.get("completed_time") is not None:
            todo.completed_time = None

    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    todo.mail_notify = data.get("mail_notify", False)
    todo.important = data.get("important", False)

    db.session.commit()

    # 添加通知
    add_notification(
        user_id,
        f"Edited task: {todo.title} (Brief: {todo.brief or (todo.content[:20] if todo.content else '')})"
    )
    return jsonify({"success": True})

@bp.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    try:
        todo = TodoModel.query.get_or_404(todo_id)
        user_id = session.get("user_id")
        user_todo_link = UserTodoModel.query.filter_by(user_id=user_id, todo_id=todo_id).first()
        if not user_todo_link:
            return jsonify({'error': 'No permission to delete this task'}), 403

        # 软删除：将任务标记为已删除
        todo.is_deleted = True
        todo.deleted_at = datetime.utcnow()
        db.session.commit()

        # 添加通知
        add_notification(user_id, f"Delete a todo: {todo.id}")
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route("/api/permanent_delete/<int:todo_id>", methods=["POST"])
def permanent_delete(todo_id):
    try:
        todo = TodoModel.query.get_or_404(todo_id)
        if todo.user_id != session.get("user_id"):
            return jsonify({'error': 'No permission to delete this task'}), 403
        
        # 永久删除：从数据库中删除记录
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route("/api/restore/<int:todo_id>", methods=["POST"])
def restore(todo_id):
    try:
        todo = TodoModel.query.get_or_404(todo_id)
        if todo.user_id != session.get("user_id"):
            return jsonify({'error': '无权限恢复此任务'}), 403
        
        # 恢复：取消删除标记
        todo.is_deleted = False
        todo.deleted_at = None
        db.session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route("/api/search")
def search_todo():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("spirit.login"))

    query = request.args.get("search", "").strip()
    filter_status = request.args.get("filter")  # completed、pending等
    sort_key = request.args.get("sort")  # deadline、start_time等

    filters = [UserTodoModel.user_id == user_id, TodoModel.is_deleted == False]
    if query:
        filters.append(
            (TodoModel.title.ilike(f"%{query}%") |
             TodoModel.content.ilike(f"%{query}%") |
             TodoModel.brief.ilike(f"%{query}%"))
        )

    query_stmt = db.session.query(TodoModel).join(UserTodoModel).filter(*filters)

    # 状态筛选
    if filter_status == "completed":
        query_stmt = query_stmt.filter(TodoModel.status == 2)
    elif filter_status == "pending":
        query_stmt = query_stmt.filter(TodoModel.status.in_([0, 1]))

    # 排序
    if sort_key in ["deadline", "start_time"]:
        query_stmt = query_stmt.order_by(getattr(TodoModel, sort_key).asc())

    matched_todos = query_stmt.all()

    # 保证 current_filter 和 current_sort 传递到模板（用于前端下拉筛选项状态展示）
    return render_template(
        "search.html",
        todo_list=matched_todos,
        keyword=query,
        current_filter=filter_status or "all",
        current_sort=sort_key or "none"
    )

@bp.route("/api/get_todo_info/<int:todo_id>", methods=["GET"])
def get_todo_info(todo_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # 支持回收站任务，允许 is_deleted=True
        todo = (
            db.session.query(TodoModel)
            .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
            .filter(
                TodoModel.id == todo_id,
                UserTodoModel.user_id == user_id
            )
            .first()
        )

        if not todo:
            return jsonify({"error": "Todo not found or no permission."}), 404

        # 确保所有字段都是字符串类型，避免 None 值
        result = {
            "id": todo.id,
            "title": str(todo.title) if todo.title else "",
            "brief": str(todo.brief) if todo.brief else "",
            "content": str(todo.content) if todo.content else "",
            "start_time": todo.start_time.strftime("%Y-%m-%d") if todo.start_time else "",
            "deadline": todo.deadline.strftime("%Y-%m-%d") if todo.deadline else "",
            "completed_time": todo.completed_time.strftime("%Y-%m-%d") if todo.completed_time else "",
            "status": todo.status,
            "priority": todo.priority,
            "mail_notify": bool(todo.mail_notify),
            "important": bool(getattr(todo, 'important', False)),
        }
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"Error fetching todo info: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
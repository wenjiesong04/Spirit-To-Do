from datetime import datetime
import pytz
from datetime import timedelta
from flask import Blueprint, render_template, session, redirect, url_for, flash, g, jsonify
from blueprints.forms import TodoForm
from exts import db
from flask import request
from models import UserModel, TodoModel, UserTodoModel
from models import FriendModel, ProjectCollaboratorModel, FriendGroupModel
from pyecharts.charts import Calendar
from pyecharts import options as opts
from sqlalchemy import func, or_
from datetime import date, timedelta

bp = Blueprint("TodoPage", __name__, url_prefix="/Spirit/TodoPage")


@bp.route("/Todo", methods=["GET"])
def todo_page():
    now = datetime.now()
    today = now.date()
    this_week_start = today - timedelta(days=today.weekday())
    this_week_end = this_week_start + timedelta(days=6)
    this_month_start = today.replace(day=1)
    this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # 获取当前登录用户
    user = getattr(g, 'user', None)
    if user is None:
        return redirect(url_for('spirit.login'))

    todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .filter(TodoModel.is_deleted == False)
        .all()
    )

    # 添加调试信息
    print(f"Todo List page: Found {len(todos)} active todos for user_id={user.id}")
    for todo in todos:
        print(f"  - todo_id={todo.id}, title='{todo.title}', is_deleted={todo.is_deleted}")

    grouped_todos = {
        "Today": [],
        "The Week": [],
        "The Month": [],
        "Customize the time range": [],
    }

    for todo in todos:
        todo.deadline_timestamp = int(todo.deadline.timestamp()) if todo.deadline else None
        added = False
        # 没有时间归到自定义
        if not (getattr(todo, 'start_time', None) and todo.deadline):
            grouped_todos["Customize the time range"].append(todo)
            continue

        s = todo.start_time.date()
        e = todo.deadline.date()

        # 今天在区间内
        if s <= today <= e:
            grouped_todos["Today"].append(todo)
            added = True
        # 本周有交集
        if not (e < this_week_start or s > this_week_end):
            grouped_todos["The Week"].append(todo)
            added = True
        # 本月有交集
        if not (e < this_month_start or s > this_month_end):
            grouped_todos["The Month"].append(todo)
            added = True
        if not added:
            grouped_todos["Customize the time range"].append(todo)

    # 查询当前用户软删除的 Todo
    trash_todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .filter(or_(TodoModel.is_deleted == True, TodoModel.is_deleted == 1))
        .order_by(TodoModel.deleted_time.desc())
        .all()
    )

    status_choices = [
        {"value": "all", "label": "All", "color": "secondary"},
        {"value": "0", "label": "Preparation", "color": "info"},
        {"value": "1", "label": "In Progress", "color": "primary"},
        {"value": "2", "label": "Completed", "color": "success"},
        {"value": "3", "label": "Overdue", "color": "danger"},
    ]
    priority_choices = [
        {"value": 0, "label": "Preparation", "color": "info"},
        {"value": 1, "label": "Normal", "color": "secondary"},
        {"value": 2, "label": "Important", "color": "warning"},
        {"value": 3, "label": "Urgent", "color": "danger"},
    ]
    selected_status = request.args.get("status", "all")

    return render_template(
        "todo/todo.html",
        grouped_todos=grouped_todos,
        status_choices=status_choices,
        priority_choices=priority_choices,
        selected_status=selected_status,
        trash_todos=trash_todos
    )


# --- 新增：todo 编辑和删除功能的路由 ---
@bp.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit(todo_id):
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Not logged in"}), 401

    todo = (db.session.query(TodoModel)
            .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
            .filter(TodoModel.id == todo_id, UserTodoModel.user_id == user.id)
            .first())
    if not todo:
        return jsonify({"error": "Todo not found or no permission."}), 404

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        todo.title = data.get('title', todo.title)
        todo.content = data.get('content', todo.content)

        # 强制类型转换，防止前端传字符串
        if 'priority' in data:
            try:
                todo.priority = int(data['priority'])
            except Exception:
                pass
        if 'status' in data:
            try:
                todo.status = int(data['status'])
            except Exception:
                pass

        deadline = data.get('deadline')
        completed_time = data.get('completed_time')
        print("DEBUG completed_time from front:", repr(completed_time))  # 打印看看实际收到的类型和值

        if 'completed_time' in data:  # 保证前端显式传递，才更新
            if completed_time:
                try:
                    if isinstance(completed_time, str):
                        try:
                            todo.completed_time = datetime.strptime(completed_time, "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            todo.completed_time = datetime.fromisoformat(completed_time)
                    else:
                        todo.completed_time = completed_time
                except Exception:
                    todo.completed_time = datetime.now()
            else:
                todo.completed_time = None
        db.session.commit()
        return jsonify({"success": True, "msg": "Todo updated successfully!"})

    # GET 返回 todo 详情（补充 completed_time, remain_seconds 字段）
    remain_seconds = None
    if todo.deadline:
        remain_seconds = int((todo.deadline - datetime.now()).total_seconds())
    todo_data = {
        "id": todo.id,
        "title": todo.title,
        "content": todo.content,
        "priority": todo.priority,
        "status": todo.status,
        "deadline": todo.deadline.strftime("%Y-%m-%d") if todo.deadline else None,
        "completed_time": todo.completed_time.strftime("%Y-%m-%d %H:%M:%S") if todo.completed_time else None,
        "remain_seconds": remain_seconds,
    }
    return todo_data


@bp.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "未登录"}), 401

    try:
        todo = TodoModel.query.get(todo_id)
        if not todo:
            return jsonify({"error": "任务未找到"}), 404

        user_todo_link = UserTodoModel.query.filter_by(user_id=user.id, todo_id=todo_id).first()
        if not user_todo_link:
            return jsonify({"error": "无权删除此任务"}), 403

        todo.is_deleted = True
        todo.deleted_time = datetime.now()
        db.session.commit()
        return jsonify({"success": True, "message": "任务已移至回收站"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route('/render_heatmap')
def render_heatmap():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # 统计每一天的 Todo 总数（按 deadline 归到那一天）
    todo_counts = (
        db.session.query(
            func.date(TodoModel.deadline).label('todo_date'),
            func.count(TodoModel.id).label('todo_count')
        )
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .group_by(func.date(TodoModel.deadline))
        .all()
    )

    todo_counts_dict = {str(row.todo_date): row.todo_count for row in todo_counts}

    def generate_calendar_data(year: int):
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        delta = timedelta(days=1)
        data = []
        while start <= end:
            d_str = start.strftime("%Y-%m-%d")
            count = todo_counts_dict.get(d_str, 0)
            data.append([d_str, count])
            start += delta
        return data

    year = 2025
    full_data = generate_calendar_data(year)

    all_counts = [count for _, count in full_data]
    max_count = max(all_counts) if all_counts else 10

    echarts_js_code = "<script>\n"
    echarts_js_code += "function initCalendar(id, data, monthRange, maxCount) {\n" \
                       "  var chart = echarts.init(document.getElementById(id));\n" \
                       "  var option = {\n" \
                       "    tooltip: {position: 'top', formatter: function (p) { return p.value[0] + ': ' + p.value[1] + ' Todos'; }},\n" \
                       "    visualMap: { min: 0, max: maxCount, inRange: { color: ['#f5f5f5', '#d0e6f7', '#8ccaf7', '#368bd6', '#1e5da3'] }, show: false },\n" \
                       "    calendar: { range: monthRange, cellSize: ['auto', 20], splitLine: { show: false },\n" \
                       "      itemStyle: { borderRadius: 6, borderColor: '#f0f0f0', borderWidth: 1 },\n" \
                       "      dayLabel: { color: '#999' }, monthLabel: { nameMap: 'en', color: '#555', fontSize: 14 }, yearLabel: { show: false } },\n" \
                       "    series: { type: 'heatmap', coordinateSystem: 'calendar', data: data }\n" \
                       "  };\n" \
                       "  chart.setOption(option);\n" \
                       "}\n"

    for month in range(1, 13):
        month_data = [d for d in full_data if int(d[0].split('-')[1]) == month]
        month_range = f"{year}-{month:02d}"

        data_js_array = "[\n" + ",\n".join([f"['{d[0]}', {d[1]}]" for d in month_data]) + "\n]"

        echarts_js_code += f"initCalendar('calendar-{['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'][month-1]}', {data_js_array}, '{month_range}', {max_count});\n"

    echarts_js_code += "</script>\n"

    html_path = "static/echarts/heat_map.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    html_final = html_template.replace("<!-- 暂时不写 ECharts 初始化，后面我们分步骤完善 -->", echarts_js_code)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_final)

    return jsonify({"success": True, "message": "Heatmap updated successfully!"})


@bp.route("/api/heatmap_data", methods=["GET"])
def heatmap_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    year = request.args.get("year", default=datetime.now().year, type=int)
    month = request.args.get("month", type=int)

    query = db.session.query(
        func.date(TodoModel.date).label("day"),
        func.count(TodoModel.id)
    ).join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id
    ).filter(UserTodoModel.user_id == user.id
    ).filter(func.strftime('%Y', TodoModel.date) == str(year))

    if month:
        query = query.filter(func.strftime('%m', TodoModel.date) == f"{month:02d}")

    query = query.group_by(func.date(TodoModel.date))
    data = query.all()

    # 日数据
    day_counts = {day: count for day, count in data}

    # 额外的月统计
    total_todos = sum(day_counts.values())
    max_day = max(day_counts.items(), key=lambda x: x[1], default=(None, 0))

    result = {
        "days": day_counts,
        "summary": {
            "total_todos": total_todos,
            "max_day": max_day[0],
            "max_day_count": max_day[1],
        }
    }

    return jsonify(result)
@bp.route("/api/dashboard_data", methods=["GET"])
def dashboard_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    month_str = request.args.get("month")  # "01", "02", ..., "12" or None

    query = db.session.query(TodoModel).join(
        UserTodoModel, UserTodoModel.todo_id == TodoModel.id
    ).filter(
        UserTodoModel.user_id == user.id
    )
    if month_str:
        query = query.filter(
            TodoModel.deadline != None,
            func.strftime('%m', TodoModel.deadline) == month_str
        )
    todos = query.all()

    # Use Asia/Shanghai local time for overdue calculation
    local_tz = pytz.timezone('Asia/Shanghai')
    now_local = datetime.now(local_tz).replace(tzinfo=None)
    sent_todo = 0
    overdue_todo = 0
    unfinished_todo = 0

    for todo in todos:
        if todo.status == 2:
            sent_todo += 1
        elif todo.status == 3:
            if todo.deadline and todo.deadline < now_local:
                overdue_todo += 1
            else:
                unfinished_todo += 1

    total_todo = len(todos)

    return jsonify({
        "sent_todo": sent_todo,
        "unfinished_todo": unfinished_todo,
        "overdue_todo": overdue_todo,
        "total_todo": total_todo
    })


@bp.route("/api/bar_chart_data", methods=["GET"])
def bar_chart_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # 获取当前用户的所有 Todo
    todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .all()
    )

    # 分类计数
    group_names = ["Recently Assigned\n(Day -14 ~ Day +14)", "Due Today", "Due Tomorrow", "Execute Later\n(After tomorrow)"]
    counts = [0, 0, 0, 0]
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    recent_start = today - timedelta(days=14)
    recent_end = today + timedelta(days=14)


    for todo in todos:
        start_date = todo.start_time.date() if todo.start_time else None

        if start_date is None:
            counts[3] += 1
        elif start_date == today:
            counts[1] += 1
        elif start_date == tomorrow:
            counts[2] += 1
        elif recent_start <= start_date <= recent_end:
            counts[0] += 1
        else:
            counts[3] += 1

    return jsonify({"labels": group_names, "data": counts})


@bp.route("/api/pie_radius_data", methods=["GET"])
def pie_radius_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # 获取当前用户的所有 Todo
    todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .all()
    )

    # 定义优先级名称映射
    priority_names = ["Preparing", "Normal", "Important", "Critical"]

    # 初始化计数
    counts = [0, 0, 0, 0]

    # 统计优先级分布
    for todo in todos:
        prio = todo.priority if todo.priority is not None else 1
        if prio < 0 or prio > 3:
            prio = 1  # 默认 Normal
        counts[prio] += 1

    # 构造前端需要的数据结构
    data = [
        {"name": priority_names[i], "value": counts[i]}
        for i in range(4)
    ]

    return jsonify(data)


# 折线图数据 API
@bp.route("/api/line_chart_data", methods=["GET"])
def line_chart_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # 计算日期区间：昨天到今天+6天，总共8天
    today = datetime.now().date()
    start_date = today - timedelta(days=1)
    date_list = [(start_date + timedelta(days=i)) for i in range(8)]
    date_str_list = [d.strftime("%m-%d") for d in date_list]

    # 初始化每天的计数
    completed_counts = {d: 0 for d in date_list}

    # 查询该用户所有完成的 todo
    todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .filter(TodoModel.completed_time != None)
        .all()
    )

    # 统计每一天完成的 todo 数
    for todo in todos:
        completed_date = todo.completed_time.date()
        if completed_date in completed_counts:
            completed_counts[completed_date] += 1

    # 组织返回数据
    count_list = [completed_counts[d] for d in date_list]

    return jsonify({
        "dates": date_str_list,
        "counts": count_list
    })


@bp.route("/api/trash_data", methods=["GET"])
def trash_data():
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    from sqlalchemy import or_
    # 查询当前用户软删除的 Todo
    todos = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .filter(or_(TodoModel.is_deleted == True, TodoModel.is_deleted == 1))
        .order_by(TodoModel.deleted_time.desc())
        .all()
    )

    data = []
    for todo in todos:
        data.append({
            "id": todo.id,
            "title": todo.title,
            "brief": todo.brief,
            "deleted_time": todo.deleted_time.strftime("%Y-%m-%d %H:%M") if todo.deleted_time else "",
            "deadline": todo.deadline.strftime("%Y-%m-%d %H:%M") if todo.deadline else "",
            "deadline_ts": int(todo.deadline.timestamp()) if todo.deadline else None,
            "priority": todo.priority,
        })

    return jsonify(data)


# 永久删除 Todo 的 API
@bp.route("/api/permanent_delete/<int:todo_id>", methods=["POST"])
def permanent_delete(todo_id):
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    todo = (
        db.session.query(TodoModel)
        .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
        .filter(UserTodoModel.user_id == user.id)
        .filter(TodoModel.id == todo_id)
        .filter(TodoModel.is_deleted == True)
        .first()
    )

    if not todo:
        return jsonify({"error": "Todo not found or no permission."}), 404

    # 删除所有 UserTodoModel 关联
    UserTodoModel.query.filter_by(todo_id=todo.id).delete()
    db.session.delete(todo)
    db.session.commit()

    return jsonify({"success": True, "message": "任务已永久删除！"})


# 还原 Todo 的 API
@bp.route("/api/restore/<int:todo_id>", methods=["POST"])
def restore(todo_id):
    user = getattr(g, 'user', None)
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        todo = (
            db.session.query(TodoModel)
            .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
            .filter(UserTodoModel.user_id == user.id)
            .filter(TodoModel.id == todo_id)
            .filter(TodoModel.is_deleted == True)
            .first()
        )

        if not todo:
            return jsonify({"error": "Todo not found or no permission."}), 404

        # 还原
        todo.is_deleted = False
        todo.deleted_time = None
        db.session.commit()
        
        # 添加调试信息
        print(f"Successfully restored todo_id={todo_id} for user_id={user.id}")
        
        # 验证恢复是否成功
        restored_todo = (
            db.session.query(TodoModel)
            .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
            .filter(UserTodoModel.user_id == user.id)
            .filter(TodoModel.id == todo_id)
            .filter(TodoModel.is_deleted == False)
            .first()
        )
        
        if restored_todo:
            print(f"Verified: todo_id={todo_id} is now restored and visible")
        else:
            print(f"Warning: todo_id={todo_id} not found after restore")

        return jsonify({"success": True, "message": "任务已恢复！"})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error restoring todo_id={todo_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/api/get_todo_info/<int:todo_id>", methods=["GET"])
def get_todo_info(todo_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # 添加日志记录
        print(f"Fetching todo info for todo_id={todo_id}, user_id={user_id}")
        
        # 使用更明确的查询
        todo = (
            db.session.query(TodoModel)
            .join(UserTodoModel, UserTodoModel.todo_id == TodoModel.id)
            .filter(
                TodoModel.id == todo_id,
                UserTodoModel.user_id == user_id,
                TodoModel.is_deleted == False
            )
            .first()
        )

        if not todo:
            print(f"Todo not found: todo_id={todo_id}, user_id={user_id}")
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
        }
        
        print(f"Successfully fetched todo info: {result}")
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Error fetching todo info: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
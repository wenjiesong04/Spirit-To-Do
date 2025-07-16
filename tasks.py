from app import app  # 或者是你创建 Flask 应用的实际文件名中的 app 对象
from flask_mail import Message
from datetime import datetime, date
from models import TodoModel, UserTodoModel, UserModel, NotificationModel
from exts import db, mail
from utils.notification import add_notification
import json
import os

# 邮件发送历史缓存文件路径
REMINDER_HISTORY_FILE = 'reminder_history.json'

def load_reminder_history():
    """加载邮件发送历史"""
    if os.path.exists(REMINDER_HISTORY_FILE):
        try:
            with open(REMINDER_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_reminder_history(history):
    """保存邮件发送历史"""
    try:
        with open(REMINDER_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存邮件历史失败: {e}")

def has_sent_reminder(todo_id, sent_date, sent_hour, history):
    """检查是否已经发送过提醒"""
    key = f"{todo_id}_{sent_date}_{sent_hour}"
    return key in history

def mark_reminder_sent(todo_id, sent_date, sent_hour, history):
    """标记提醒已发送"""
    key = f"{todo_id}_{sent_date}_{sent_hour}"
    history[key] = {
        "todo_id": todo_id,
        "sent_date": sent_date,
        "sent_hour": sent_hour,
        "sent_time": datetime.now().isoformat()
    }

def register_tasks(scheduler):
    @scheduler.task('cron', id='reminder_task', hour='8,18')
    def reminder_task():
        with app.app_context():
            now = datetime.now()
            current_date = now.date().isoformat()
            current_hour = now.hour
            
            print(f"🟢 邮件提醒任务触发于 {now}")
            
            # 加载发送历史
            reminder_history = load_reminder_history()
            
            # 获取所有需要邮件提醒的未完成任务
            todos = TodoModel.query.filter(
                TodoModel.mail_notify == True, 
                TodoModel.completed_time == None,
                TodoModel.is_deleted == False
            ).all()
            
            print(f"📌 找到 {len(todos)} 个需要提醒的任务")

            for todo in todos:
                days_left = (todo.deadline.date() - now.date()).days
                print(f"🔍 检查任务: {todo.title}, 距离截止日期 {days_left} 天")
                
                # 判断是否需要发送提醒
                should_remind = False
                
                # 新的提醒规则：
                # 1. deadline < 3天 && >= 1天：每天提醒一次（只在8点）
                # 2. deadline < 1天：每天提醒两次（8点和18点）
                # 3. deadline < 0天：超时后只提醒一次（在deadline后一天）
                
                if days_left >= 1 and days_left <= 3:
                    # 距离截止日期1-3天，只在早上8点提醒
                    if current_hour == 8:
                        should_remind = True
                elif days_left == 0:
                    # 截止日期当天，8点和18点都提醒
                    if current_hour in [8, 18]:
                        should_remind = True
                elif days_left == -1:
                    # 超时后一天，只提醒一次（在8点）
                    if current_hour == 8:
                        should_remind = True
                
                # 检查是否已经发送过提醒
                if should_remind and has_sent_reminder(todo.id, current_date, current_hour, reminder_history):
                    print(f"⏭️ 任务 '{todo.title}' 在 {current_date} {current_hour}点 已经发送过提醒，跳过")
                    should_remind = False
                
                if should_remind:
                    # 获取用户信息
                    link = UserTodoModel.query.filter_by(todo_id=todo.id).first()
                    if not link:
                        print(f"⚠️ 未找到任务 '{todo.title}' (ID: {todo.id}) 的用户关联")
                        continue
                    
                    user = UserModel.query.get(link.user_id)
                    if not user or not user.email:
                        print(f"⚠️ 未找到任务 '{todo.title}' 的有效用户或邮箱")
                        continue
                    
                    print(f"📧 准备向 {user.email} 发送任务 '{todo.title}' 的提醒")
                    
                    # 构建邮件主题和内容
                    if days_left < 0:
                        subject = f"[Spirit Reminder] '{todo.title}' is overdue!"
                        urgency_text = "⚠️ This task is overdue. Please take action as soon as possible!"
                    elif days_left == 0:
                        subject = f"[Spirit Reminder] '{todo.title}' is due today!"
                        urgency_text = "🚨 This task is due today. Please complete it as soon as possible!"
                    else:
                        subject = f"[Spirit Reminder] '{todo.title}' is due in {days_left} day(s)"
                        urgency_text = f"⏰ {days_left} day(s) remaining. Please stay on track!"

                    # 构建邮件内容，参考多邻国的提醒风格
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        sender="Spirit Todo <3518648435@qq.com>",
                        html=f"""
                        <html>
                        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px;">
                            <div style="max-width: 600px; margin: auto; background: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden;">
                                <!-- Header -->
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                                    <h1 style="margin: 0; font-size: 28px; font-weight: 300;">👻 Spirit Todo</h1>
                                    <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">Keep your productivity streak alive!</p>
                                </div>
                                
                                <!-- Main content -->
                                <div style="padding: 40px 30px;">
                                    <div style="text-align: center; margin-bottom: 30px;">
                                        <div style="display: inline-block; background: #f8f9fa; padding: 20px; border-radius: 15px; border-left: 5px solid #667eea;">
                                            <h2 style="margin: 0 0 10px 0; color: #333; font-size: 24px;">{urgency_text}</h2>
                                            <h3 style="margin: 0; color: #667eea; font-size: 20px;">{todo.title}</h3>
                                        </div>
                                    </div>
                                    
                                    <div style="background: #f8f9fa; padding: 25px; border-radius: 15px; margin-bottom: 25px;">
                                        <h4 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">📋 Task Details</h4>
                                        <p style="margin: 0 0 10px 0; color: #666;"><strong>Deadline:</strong> {todo.deadline.strftime('%B %d, %Y %H:%M')}</p>
                                        <p style="margin: 0 0 10px 0; color: #666;"><strong>Time Left:</strong> {'Overdue' if days_left < 0 else f'{days_left} day(s)'}</p>
                                        {f'<p style="margin: 0 0 10px 0; color: #666;"><strong>Brief:</strong> {todo.brief}</p>' if todo.brief else ''}
                                        {f'<p style="margin: 0 0 10px 0; color: #666;"><strong>Content:</strong> {todo.content}</p>' if todo.content else ''}
                                    </div>
                                    
                                    <div style="text-align: center; margin: 30px 0;">
                                        <div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 16px;">
                                            🎯 Take Action Now
                                        </div>
                                    </div>
                                    
                                    <div style="background: #e8f4fd; padding: 20px; border-radius: 15px; border-left: 5px solid #667eea;">
                                        <p style="margin: 0; color: #333; font-size: 14px;">
                                            💡 <strong>Tip:</strong> Focus on one task at a time. Completing this will keep your productivity streak alive!
                                        </p>
                                    </div>
                                </div>
                                
                                <!-- Footer -->
                                <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px;">
                                    <p style="margin: 0;">From the Spirit Todo Team</p>
                                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Keep your momentum going. Don’t break the streak!</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                    )

                    try:
                        mail.send(msg)
                        print(f"✅ 成功向 {user.email} 发送任务 '{todo.title}' 的提醒邮件")

                        # 标记提醒已发送
                        mark_reminder_sent(todo.id, current_date, current_hour, reminder_history)

                        # 添加系统通知
                        if days_left < 0:
                            notify_content = f"The task '{todo.title}' is overdue. Please check it ASAP!"
                        elif days_left == 0:
                            notify_content = f"The task '{todo.title}' is due today. Please handle it soon!"
                        else:
                            notify_content = f"The task '{todo.title}' is due in {days_left} day(s). Stay on track!"
                        
                        # 检查是否已有相同内容的通知
                        exists = NotificationModel.query.filter_by(
                            user_id=user.id,
                            content=notify_content
                        ).first()
                        
                        if not exists:
                            add_notification(user.id, notify_content)
                            
                    except Exception as e:
                        print(f"❌ 向 {user.email} 发送提醒邮件失败: {e}")
            
            # 保存发送历史
            save_reminder_history(reminder_history)
            print(f"💾 邮件发送历史已保存")
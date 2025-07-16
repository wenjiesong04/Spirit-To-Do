# Spirit Todo 邮件提醒功能

## 功能概述

Spirit Todo 现在支持智能邮件提醒功能，帮助用户及时处理任务，避免错过截止日期。

## 提醒规则

### 1. 距离截止日期 1-3 天
- **提醒频率**: 每天一次
- **提醒时间**: 早上 8:00
- **邮件主题**: `[Spirit 提醒] 『任务标题』还有 X 天截止`

### 2. 截止日期当天
- **提醒频率**: 每天两次
- **提醒时间**: 早上 8:00 和晚上 18:00
- **邮件主题**: `[Spirit 提醒] 『任务标题』今天截止！`

### 3. 超期后
- **提醒频率**: 只提醒一次
- **提醒时间**: 超期后第一天的早上 8:00
- **邮件主题**: `[Spirit 提醒] 『任务标题』已超期！`

## 防重复发送机制

系统使用文件缓存方式记录邮件发送历史，确保：
- 同一个任务在同一个时间点不会重复发送
- 历史记录保存在 `reminder_history.json` 文件中
- 支持定期清理过期记录

## 邮件模板特色

邮件模板参考多邻国的提醒风格，包含：
- 🎨 现代化的渐变设计
- 📋 清晰的任务详情展示
- ⏰ 醒目的时间提醒
- 💡 激励性的小贴士
- 🎯 行动号召按钮

## 文件说明

### 核心文件
- `tasks.py`: 邮件提醒任务实现
- `reminder_history.json`: 邮件发送历史记录（自动生成）

### 工具脚本
- `test_reminder.py`: 测试邮件提醒逻辑
- `cleanup_reminder_history.py`: 清理过期历史记录

## 使用方法

### 1. 启用邮件提醒
在创建或编辑任务时，勾选 "Mail Notify" 选项。

### 2. 测试提醒逻辑
```bash
python test_reminder.py
```

### 3. 查看历史统计
```bash
python cleanup_reminder_history.py stats
```

### 4. 清理过期记录
```bash
# 清理超过30天的记录（默认）
python cleanup_reminder_history.py cleanup

# 清理超过指定天数的记录
python cleanup_reminder_history.py cleanup 60
```

## 技术实现

### 定时任务
- 使用 APScheduler 定时任务
- 每天 8:00 和 18:00 执行
- 自动检查需要提醒的任务

### 防重复机制
- 使用 JSON 文件存储发送历史
- 键格式: `{todo_id}_{date}_{hour}`
- 支持并发安全

### 邮件发送
- 使用 Flask-Mail 发送邮件
- 支持 HTML 格式
- 自动处理发送失败

## 配置要求

确保在 `config.py` 中正确配置邮箱信息：
```python
MAIL_SERVER = "smtp.qq.com"
MAIL_USE_SSL = True
MAIL_PORT = 465
MAIL_USERNAME = "your_email@qq.com"
MAIL_PASSWORD = "your_app_password"
MAIL_DEFAULT_SENDER = "your_email@qq.com"
```

## 注意事项

1. **邮箱配置**: 确保使用正确的 SMTP 配置和授权码
2. **定时任务**: 确保服务器时间准确
3. **文件权限**: 确保应用有读写 `reminder_history.json` 的权限
4. **定期清理**: 建议每周运行一次清理脚本，避免历史文件过大

## 故障排除

### 邮件发送失败
- 检查邮箱配置是否正确
- 确认网络连接正常
- 查看应用日志获取详细错误信息

### 重复发送问题
- 检查 `reminder_history.json` 文件是否正常
- 确认文件权限设置正确
- 重启应用后重试

### 定时任务不执行
- 检查 APScheduler 是否正确启动
- 确认服务器时间设置
- 查看应用启动日志

## 更新日志

### v1.0.0 (2025-06-22)
- ✨ 新增智能邮件提醒功能
- 🎨 采用多邻国风格的邮件模板
- 🛡️ 实现防重复发送机制
- 📊 添加历史记录管理功能
- 🧪 提供完整的测试工具 
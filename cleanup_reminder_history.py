#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理邮件提醒历史记录脚本
定期清理超过30天的历史记录，避免文件过大
"""

import os
import json
from datetime import datetime, timedelta

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

def cleanup_old_records(days_to_keep=30):
    """清理超过指定天数的历史记录"""
    print(f"🧹 开始清理超过 {days_to_keep} 天的邮件历史记录")
    
    # 加载历史记录
    history = load_reminder_history()
    
    if not history:
        print("📭 没有找到邮件历史记录")
        return
    
    print(f"📊 清理前记录数量: {len(history)}")
    
    # 计算截止日期
    cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
    cutoff_date_str = cutoff_date.isoformat()
    
    print(f"🗓️ 清理截止日期: {cutoff_date_str}")
    
    # 需要删除的记录
    records_to_delete = []
    
    for key, record in history.items():
        sent_date_str = record.get('sent_date', '')
        if sent_date_str and sent_date_str < cutoff_date_str:
            records_to_delete.append(key)
    
    # 删除旧记录
    for key in records_to_delete:
        del history[key]
        print(f"🗑️ 删除记录: {key}")
    
    print(f"📊 清理后记录数量: {len(history)}")
    print(f"🗑️ 共删除 {len(records_to_delete)} 条记录")
    
    # 保存清理后的历史记录
    save_reminder_history(history)
    print("💾 清理后的历史记录已保存")

def show_history_stats():
    """显示历史记录统计信息"""
    history = load_reminder_history()
    
    if not history:
        print("📭 没有邮件历史记录")
        return
    
    print(f"📊 邮件历史记录统计")
    print("=" * 40)
    print(f"总记录数: {len(history)}")
    
    # 按日期统计
    date_stats = {}
    for record in history.values():
        sent_date = record.get('sent_date', '')
        if sent_date:
            date_stats[sent_date] = date_stats.get(sent_date, 0) + 1
    
    print(f"\n按日期统计:")
    for date_str, count in sorted(date_stats.items()):
        print(f"  {date_str}: {count} 条记录")
    
    # 按小时统计
    hour_stats = {}
    for record in history.values():
        sent_hour = record.get('sent_hour', 0)
        hour_stats[sent_hour] = hour_stats.get(sent_hour, 0) + 1
    
    print(f"\n按小时统计:")
    for hour, count in sorted(hour_stats.items()):
        print(f"  {hour}点: {count} 条记录")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleanup_old_records(days)
        elif command == "stats":
            show_history_stats()
        else:
            print("用法: python cleanup_reminder_history.py [cleanup|stats] [days]")
    else:
        # 默认执行清理
        cleanup_old_records()
        print("\n" + "=" * 40)
        show_history_stats() 
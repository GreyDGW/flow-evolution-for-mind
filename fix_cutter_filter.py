#!/usr/bin/env python3
# -*- coding: utf-8 -*-

path = 'batch_session_cutter.py'
with open(path, 'r') as f:
    content = f.read()

# 修复 1: find_uncut_sessions 增加 is_system_noise 过滤
old1 = '''        c.execute("""
             SELECT session_id, COUNT(*) as msg_count
             FROM sessions
             WHERE timestamp > ?
               AND session_id NOT LIKE '%#%'
               AND role IN ('user', 'assistant')
               AND (is_auto_push = 0 OR is_auto_push IS NULL)
             GROUP BY session_id
             HAVING COUNT(*) >= 2
         """, (cutoff_time,))'''

new1 = '''        c.execute("""
             SELECT session_id, COUNT(*) as msg_count
             FROM sessions
             WHERE timestamp > ?
               AND session_id NOT LIKE '%#%'
               AND role IN ('user', 'assistant')
               AND (is_auto_push = 0 OR is_auto_push IS NULL)
               AND (is_system_noise = 0 OR is_system_noise IS NULL)
             GROUP BY session_id
             HAVING COUNT(*) >= 2
         """, (cutoff_time,))'''

if old1 in content:
    content = content.replace(old1, new1)
    print("✅ 修复 1/2: find_uncut_sessions 已增加 is_system_noise 过滤")
else:
    print("⚠️ 修复 1: 未找到 find_uncut_sessions 目标代码，请手动检查")

# 修复 2: 如果 get_session_messages 在 cutter 中，同步增加过滤
old2 = '''    c.execute("""
         SELECT role, content_text, timestamp, agent_id
         FROM sessions
         WHERE session_id = ?
           AND role IN ('user', 'assistant')
           AND (is_auto_push = 0 OR is_auto_push IS NULL)
         ORDER BY timestamp
     """, (session_id,))'''

new2 = '''    c.execute("""
         SELECT role, content_text, timestamp, agent_id
         FROM sessions
         WHERE session_id = ?
           AND role IN ('user', 'assistant')
           AND (is_auto_push = 0 OR is_auto_push IS NULL)
           AND (is_system_noise = 0 OR is_system_noise IS NULL)
         ORDER BY timestamp
     """, (session_id,))'''

if old2 in content:
    content = content.replace(old2, new2)
    print("✅ 修复 2/2: get_session_messages 已增加 is_system_noise 过滤")
else:
    print("ℹ️ 修复 2: get_session_messages 不在 cutter 中或格式不同，跳过")

with open(path, 'w') as f:
    f.write(content)

print("✅ 文件已保存")

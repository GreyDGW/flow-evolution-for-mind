import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 最近60秒
c.execute("""
    SELECT session_id, role, substr(content_text, 1, 60), timestamp
    FROM sessions
    WHERE timestamp > datetime('now', '-60 seconds')
    ORDER BY timestamp DESC
""")
rows = c.fetchall()

print("最近60秒新增消息: %d 条" % len(rows))
for sid, role, content, ts in rows:
    print("  [%s] %s | %s | %s" % (ts, role[:8], content or '[空]', sid[:16]))
conn.close()

print("\n=== 精确搜索 '2332' ===")
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()
c.execute("""
    SELECT session_id, role, substr(content_text, 1, 100), timestamp
    FROM sessions
    WHERE content_text LIKE '%2332%'
    ORDER BY timestamp DESC
    LIMIT 3
""")
rows = c.fetchall()
print("找到 %d 条含 '2332' 的记录" % len(rows))
for sid, role, content, ts in rows:
    print("  时间: %s" % ts)
    print("  角色: %s" % role)
    print("  内容: %s" % content)
    print("  ---")
conn.close()

print("\n=== 验证 watchdog 状态文件 ===")
import os
state = ".collect_state.json"
if os.path.exists(state):
    mtime = os.path.getmtime(state)
    print("状态文件最后修改: %s" % datetime.fromtimestamp(mtime).strftime('%H:%M:%S'))
    print("当前时间: %s" % datetime.now().strftime('%H:%M:%S'))
    diff = (datetime.now().timestamp() - mtime)
    if diff < 60:
        print("✅ 状态文件在60秒内更新过，watchdog在工作")
    else:
        print("⚠️ 状态文件超过60秒未更新")
else:
    print("❌ 状态文件不存在")

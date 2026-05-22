import sqlite3, json, re

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 取5条不同长度的样本
c.execute("SELECT id, content_text, content_length FROM sessions ORDER BY content_length DESC LIMIT 5")
print("=== sessions 样本（最长5条）===")
for sid, text, length in c.fetchall():
    print("\nID: %d | 长度: %d" % (sid, length))
    print("前500字:")
    print(text[:500])
    print("-" * 40)

# 再取5条最短的
c.execute("SELECT id, content_text, content_length FROM sessions ORDER BY content_length ASC LIMIT 5")
print("\n=== sessions 样本（最短5条）===")
for sid, text, length in c.fetchall():
    print("\nID: %d | 长度: %d" % (sid, length))
    print("完整内容:")
    print(text)
    print("-" * 40)

conn.close()

import sqlite3, json

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

c.execute("SELECT id, content_text, content_length FROM sessions ORDER BY content_length DESC LIMIT 5")
print("=== sessions 表样本（最长5条）===")
for row in c.fetchall():
    sid = str(row[0])
    text = row[1]
    length = row[2]
    print("\nID: %s | 长度: %d" % (sid[:20], length))
    print("前300字: %s" % str(text)[:300])
    
    # 尝试解析 JSON
    try:
        data = json.loads(text)
        print("✅ JSON解析成功 | 类型: %s" % type(data).__name__)
        if isinstance(data, list) and len(data) > 0:
            print("  数组长度: %d | 第1项: %s" % (len(data), type(data[0]).__name__))
            if isinstance(data[0], dict):
                print("  keys: %s" % str(list(data[0].keys())))
        elif isinstance(data, dict):
            print("  Dict keys: %s" % str(list(data.keys())))
    except Exception as e:
        print("❌ 非JSON: %s" % str(e)[:60])

conn.close()

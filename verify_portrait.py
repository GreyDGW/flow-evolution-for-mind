import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()
c.execute("SELECT prompt_version, COUNT(*), COUNT(portrait_label), COUNT(style_pace) FROM session_analyses GROUP BY prompt_version")
for row in c.fetchall():
    ver, total, p_count, s_count = row
    status = '✅' if p_count == total else '❌'
    print(f'{status} {ver}: 共{total}条 | portrait={p_count} | style={s_count}')
conn.close()
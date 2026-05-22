import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print('=== 问题1：检查 evidence 中是否有引号 ===')
c.execute("SELECT goal_evidence FROM session_analyses WHERE prompt_version='v8.5' LIMIT 5")
for i, row in enumerate(c.fetchall()):
    ev = row[0]
    has_double = '"' in ev
    has_single = "'" in ev
    print(f'\n记录{i+1}: 长度={len(ev)}')
    print(f'  英文双引号: {has_double} | 英文单引号: {has_single}')
    print(f'  前150字: {ev[:150]}...')

conn.close()
import sqlite3

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print('=' * 50)
print('🧪 最终验证')
print('=' * 50)

# 1. 重复记录检查
c.execute('SELECT session_id, COUNT(*) as cnt FROM session_analyses GROUP BY session_id HAVING cnt > 1')
dups = c.fetchall()
print(f'\n【1】重复记录: {len(dups)} 个 session')
for sid, cnt in dups:
    print(f'  ⚠️ {sid[:20]}... : {cnt}条')
if not dups:
    print('  ✅ 无重复记录')

# 2. 4/20 证据长度分布
c.execute('''SELECT length(goal_evidence), length(closure_evidence), length(flow_evidence), length(cognition_evidence) FROM session_analyses sa JOIN sessions s ON sa.session_id = s.session_id WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59' AND sa.prompt_version = 'v8.5' ''')
rows = c.fetchall()
all_lens = [x for row in rows for x in row]
if all_lens:
    over300 = len([x for x in all_lens if x > 300])
    print(f'\n【2】4/20 证据: 平均{sum(all_lens)//len(all_lens)}字, 范围{min(all_lens)}-{max(all_lens)}字, 超300字:{over300}条')

# 3. 报告回归测试
from plugin.report_assembler import ReportAssembler
import re
asm = ReportAssembler()
r20 = asm.generate_flow_report(start='2026-04-20 00:00:00', end='2026-04-20 23:59:59')
print(f'\n【3】回归测试:')
print(f'  报告长度: {len(r20)} 字')
data_insufficient = r20.count("数据不足")
print(f'  数据不足: {data_insufficient} 次 {"❌" if data_insufficient > 0 else "✅"}')

# 检查引语
if '>' in r20:
    idx = r20.find('>') + 1
    end = r20.find('\n', idx)
    quote = r20[idx:end].strip()
    print(f'  引语: "{quote[:50]}..." {"✅" if len(quote.strip()) > 5 else "❌ 为空"}')

# 检查原文引用（支持中英文混合引号）
quotes = re.findall(r'["\u201c\u201c]([^"\u201d\u201d]{10,60})["\u201d\u201d]', r20)
print(f'  原文引用: {len(quotes)} 处 {"✅" if len(quotes) > 0 else "⚠️"}')

conn.close()
print('\n' + '=' * 50)
print('🎉 修复完成')
print('=' * 50)
#!/usr/bin/env python3
"""
Flow Ecosystem - 全链路重建脚本
一键执行：备份 → 清库 → 导入 → 切割 → 分析 → 验证
"""

import os, sys, subprocess, sqlite3, time, shutil
from datetime import datetime

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(PROJECT, 'data', 'flow_ecosystem.db')
STATE = os.path.join(PROJECT, '.collect_state.json')

def run(cmd, t=600):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ▶ {cmd[:70]}...")
    r = subprocess.run(cmd, cwd=PROJECT, shell=True, capture_output=True, text=True, timeout=t)
    if r.returncode != 0:
        print(f"❌ 失败: {r.stderr[-400:]}")
        sys.exit(1)
    print(r.stdout[-700:] if len(r.stdout) > 700 else r.stdout)

def db(sql):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute(sql)
    result = c.fetchall()
    conn.close()
    return result

def db_script(sql):
    conn = sqlite3.connect(DB)
    conn.executescript(sql)
    conn.commit(); conn.close()

# 1. 备份
print("=" * 50)
print("Flow Ecosystem - 全链路重建")
print("=" * 50)
backup = f"data/flow_ecosystem_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
if os.path.exists(DB):
    shutil.copy2(DB, os.path.join(PROJECT, backup))
    print(f"✅ 备份: {backup}")

# 2. 清库 + 重置状态
print("\n[2/6] 清库 + 重置导入状态")
if os.path.exists(STATE): os.remove(STATE)
db_script("""
    DELETE FROM sessions; DELETE FROM session_analyses;
    DELETE FROM kv_store; DELETE FROM agent_goals;
    DELETE FROM sqlite_sequence WHERE name='session_analyses';
""")
for n, c in db("SELECT 'sessions',COUNT(*) FROM sessions UNION ALL SELECT 'analyses',COUNT(*) FROM session_analyses"):
    print(f"  {n}: {c}")

# 3. 全量导入
print("\n[3/6] 全量导入")
run("python3 adapters/openclaw/scripts/init.py", t=300)
r = db("""
    SELECT COUNT(*), COUNT(DISTINCT session_id), COUNT(DISTINCT agent_id),
           SUM(CASE WHEN role='user' THEN 1 ELSE 0 END),
           SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END)
    FROM sessions WHERE (is_system_noise=0 OR is_system_noise IS NULL)
      AND (is_auto_push=0 OR is_auto_push IS NULL)
""")[0]
total, sessions, agents, u, a = r
print(f"✅ 导入: {total}条 | {sessions}session | {agents}agent | U:A={round(u/a,2) if a else 0}")
if total < 100: sys.exit(1)

# 4. 全量切割（调用内部函数而非命令行）
print("\n[4/6] 全量切割")
# 直接调用 batch_session_cutter 的 Python 函数，避免 __main__ 入口问题
cut_result = run("""
python3 -c "
import sys
sys.path.insert(0, '.')
from batch_session_cutter import find_uncut_sessions, batch_cut
uncut = find_uncut_sessions(db_path='data/flow_ecosystem.db')
print(f'[AutoCut] Found {len(uncut)} uncut sessions')
for sid in uncut:
    batch_cut(session_id=sid, db_path='data/flow_ecosystem.db')
    print(f'  cut: {sid}')
"
""", t=300)
cut = db("""
    SELECT COUNT(DISTINCT session_id) FROM sessions
    WHERE session_id LIKE '%#%' AND (is_system_noise=0 OR is_system_noise IS NULL)
      AND (is_auto_push=0 OR is_auto_push IS NULL)
""")[0][0]
print(f"✅ 切割子session: {cut} 个")

# 5. 全量分析（遍历所有有数据的日期）
print("\n[5/6] 全量分析")
dates = db("""
    SELECT DISTINCT date(timestamp) FROM sessions
    WHERE (is_system_noise=0 OR is_system_noise IS NULL)
      AND (is_auto_push=0 OR is_auto_push IS NULL)
      AND role IN ('user','assistant')
    ORDER BY date(timestamp)
""")
print(f"   发现 {len(dates)} 个日期需要分析")
for i, (dt,) in enumerate(dates, 1):
    date_str = str(dt)
    print(f"   [{i}/{len(dates)}] 分析 {date_str}...")
    run(f"python3 batch_analyze_with_save.py --date '{date_str}'", t=600)

# 6. 验证
print("\n[6/6] 质量验证")
total_s = db("""
    SELECT COUNT(DISTINCT s.session_id) FROM sessions s
    WHERE (s.is_system_noise=0 OR s.is_system_noise IS NULL)
      AND (s.is_auto_push=0 OR s.is_auto_push IS NULL)
      AND s.role IN ('user','assistant')
""")[0][0]
analyzed = db("""
    SELECT COUNT(DISTINCT sa.session_id) FROM session_analyses sa
    JOIN sessions s ON sa.session_id=s.session_id
    WHERE (s.is_system_noise=0 OR s.is_system_noise IS NULL)
      AND (s.is_auto_push=0 OR s.is_auto_push IS NULL)
""")[0][0]
rate = round(analyzed/total_s*100, 1) if total_s else 0
ev = db("""
    SELECT ROUND(AVG(LENGTH(goal_evidence)),0), ROUND(AVG(LENGTH(closure_evidence)),0),
           ROUND(AVG(LENGTH(flow_evidence)),0), ROUND(AVG(LENGTH(cognition_evidence)),0)
    FROM session_analyses
""")[0]

print(f"\n📊 验收报告")
print(f"  分析成功率: {rate}% ({analyzed}/{total_s}) {'✅' if rate>=80 else '❌'}")
print(f"  证据长度: 目标{ev[0]} | 闭环{ev[1]} | 心流{ev[2]} | 认知{ev[3]}")
passed = rate >= 80 and all(e and e >= 50 for e in ev)
print(f"\n{'🎉 Phase 1 全链路通过！' if passed else '⚠️ 部分未达标'}")

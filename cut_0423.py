#!/usr/bin/env python3
"""切割4月23日的session"""

import sqlite3
import sys
sys.path.insert(0, '.')

from plugin.session.session_cutter import SemanticSessionCutter

DB_PATH = 'data/flow_ecosystem.db'

def batch_cut(target_date):
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    c = conn.cursor()

    c.execute("""
        UPDATE sessions
        SET session_id = substr(session_id, 1, instr(session_id, '#') - 1)
        WHERE date(timestamp) = ? AND session_id LIKE '%#%'
    """, (target_date,))
    restored = c.rowcount
    conn.commit()
    print(f"  🔄 已恢复 {restored} 条记录")

    c.execute("""
        SELECT DISTINCT session_id
        FROM sessions
        WHERE date(timestamp) = ?
    """, (target_date,))
    sessions = [r[0] for r in c.fetchall()]
    conn.close()

    print(f"📅 {target_date} 共 {len(sessions)} 个原始 session")

    cutter = SemanticSessionCutter()

    for sid in sessions:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT role, content_text, timestamp
            FROM sessions
            WHERE session_id = ?
            ORDER BY timestamp
        """, (sid,))
        msgs = [{'role': r['role'], 'content': r['content_text'] or '', 'timestamp': r['timestamp']} for r in c.fetchall()]
        conn.close()

        if not msgs:
            continue

        print(f"\n📥 Session {sid[:20]}... | {len(msgs)} 条消息")

        try:
            segments = cutter.cut_sessions(msgs, threshold=0.15)
            print(f"  🔪 切割结果: {len(segments)} 个子 session")

            if len(segments) > 1:
                conn = sqlite3.connect(DB_PATH, timeout=60)
                c = conn.cursor()
                for idx, seg in enumerate(segments):
                    new_sid = sid if idx == 0 else f"{sid}#{idx + 1}"
                    for m in seg:
                        c.execute("UPDATE sessions SET session_id = ? WHERE id = (SELECT id FROM sessions WHERE session_id = ? AND content_text = ? LIMIT 1)",
                                  (new_sid, sid, m['content']))
                conn.commit()
                conn.close()
                print(f"  ✅ 已更新数据库")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    print(f"\n🎉 完成！")

if __name__ == '__main__':
    batch_cut('2026-04-23')

#!/usr/bin/env python3
"""批量分析指定日期所有 session 的四维指标"""

import sqlite3
import sys
import argparse
sys.path.insert(0, '.')

from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

DB_PATH = 'data/flow_ecosystem.db'

def analyze_date(target_date: str):
    """分析指定日期的所有 session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT session_id, COUNT(*) as cnt,
               MIN(timestamp) as first_ts
        FROM sessions
        WHERE date(timestamp) = ?
        GROUP BY session_id
        ORDER BY first_ts
    """, (target_date,))
    sessions = [r[0] for r in c.fetchall()]
    conn.close()

    if not sessions:
        print(f"❌ {target_date} 没有找到 session")
        return

    print(f"📅 {target_date} 共 {len(sessions)} 个session待分析")

    llm = DeepSeekLLMClient()
    analyzer = SessionAnalyzer(llm)

    success_count = 0
    fail_count = 0

    for idx, sid in enumerate(sessions, 1):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT role, content_text, timestamp
            FROM sessions
            WHERE session_id = ?
            ORDER BY timestamp
        """, (sid,))
        msgs = [{'role': r['role'], 'content_text': r['content_text'], 'timestamp': r['timestamp']} for r in c.fetchall()]
        conn.close()

        if not msgs:
            continue

        display_sid = sid[:35] + '...' if len(sid) > 35 else sid
        print(f"\n[{idx}/{len(sessions)}] 🔍 {display_sid} ({len(msgs)}条)")

        try:
            results = analyzer.analyze_batch(msgs, sid, gap_minutes=15)

            if results:
                for r in results:
                    ga = r.goal_alignment if hasattr(r, 'goal_alignment') else '?'
                    ci = r.closure_index if hasattr(r, 'closure_index') else '?'
                    fd = r.flow_depth if hasattr(r, 'flow_depth') else '?'
                    cg = r.cognition_growth if hasattr(r, 'cognition_growth') else '?'
                    pl = r.portrait_label if hasattr(r, 'portrait_label') else '?'

                    ev = ''
                    if hasattr(r, 'goal_evidence') and r.goal_evidence:
                        ev = r.goal_evidence[:60] + '...' if len(r.goal_evidence) > 60 else r.goal_evidence

                    print(f"  ✅ 4维: {ga}/{ci}/{fd}/{cg}")
                    print(f"     🎭 {pl}")
                    print(f"     📝 {ev}")
                success_count += 1
            else:
                print(f"  ⚠️ 无分析结果")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:80]}")
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"🎉 分析完成！成功: {success_count} | 失败: {fail_count} | 总计: {len(sessions)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量分析 session 四维指标')
    parser.add_argument('--date', '-d', required=True, help='目标日期 (YYYY-MM-DD)')
    args = parser.parse_args()

    analyze_date(args.date)

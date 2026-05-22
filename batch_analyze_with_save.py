#!/usr/bin/env python3
"""批量分析指定日期所有 session 的四维指标（带保存）"""

import sqlite3
import sys
import argparse
sys.path.insert(0, '.')

from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

DB_PATH = 'data/flow_ecosystem.db'

INSERT_SQL = """
INSERT OR REPLACE INTO session_analyses (
    session_id, agent_id, goal_alignment, closure_index, flow_depth, cognition_growth,
    goal_evidence, closure_evidence, flow_evidence, cognition_evidence,
    llm_model, llm_latency_ms, prompt_version,
    portrait_label, portrait_description, portrait_suggestion, portrait_rule_insight,
    style_pace, style_depth, style_tone, style_friction,
    created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def save_analysis(result, db_path):
    """保存分析结果到数据库"""
    # V7.8-9-6: 使用 session 原始时间戳作为 created_at
    conn_tmp = sqlite3.connect(db_path)
    c_tmp = conn_tmp.cursor()
    c_tmp.execute("SELECT MIN(timestamp) FROM sessions WHERE session_id = ? AND (is_system_noise = 0 OR is_system_noise IS NULL)", (result.session_id,))
    ts_row = c_tmp.fetchone()
    session_timestamp = ts_row[0] if ts_row and ts_row[0] else None
    conn_tmp.close()

    # 修复：写入前校验 evidence 长度
    evidence_fields = [
        ('goal_evidence', result.goal_evidence),
        ('closure_evidence', result.closure_evidence),
        ('flow_evidence', result.flow_evidence),
        ('cognition_evidence', result.cognition_evidence),
    ]
    
    for name, ev in evidence_fields:
        if not ev or len(ev) < 20:
            print(f"⚠️ 证据校验失败: {name} 长度 {len(ev) if ev else 0} 字，低于 20 字下限。拒绝写入。")
            return False
        if len(ev) > 300:
            print(f"ℹ️ 证据截断: {name} 长度 {len(ev)} 字，超过 300 字上限，截断至 300 字。")
            setattr(result, name, ev[:300])
    
    # V7.8-9-2: 从 sessions 表获取 agent_id
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT agent_id FROM sessions WHERE session_id = ? AND (is_system_noise = 0 OR is_system_noise IS NULL) LIMIT 1", (result.session_id,))
    row = c.fetchone()
    agent_id = row[0] if row and row[0] else None

    c.execute(INSERT_SQL, (
        result.session_id,
        agent_id,
        result.goal_alignment,
        result.closure_index,
        result.flow_depth,
        result.cognition_growth,
        result.goal_evidence,
        result.closure_evidence,
        result.flow_evidence,
        result.cognition_evidence,
        'deepseek-chat',
        0,
        'v1',
        result.portrait_label,
        result.portrait_description,
        result.portrait_suggestion,
        result.portrait_rule_insight,
        result.style_pace,
        result.style_depth,
        result.style_tone,
        result.style_friction,
            session_timestamp))
    conn.commit()
    conn.close()
    return True


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
            WHERE session_id = ? AND role IN ('user', 'assistant') AND (is_auto_push = 0 OR is_auto_push IS NULL) AND (is_system_noise = 0 OR is_system_noise IS NULL)
            ORDER BY timestamp
        """, (sid,))
        msgs = [{'role': r['role'], 'content_text': r['content_text'], 'timestamp': r['timestamp']} for r in c.fetchall()]
        msgs = _merge_streaming_segments(msgs)

        # V7.8-9-6: 获取 agent_id 用于目标对齐度外部参照（必须在 conn.close() 之前）
        c.execute("SELECT DISTINCT agent_id FROM sessions WHERE session_id = ? AND (is_system_noise = 0 OR is_system_noise IS NULL) LIMIT 1", (sid,))
        row = c.fetchone()
        session_agent_id = row[0] if row and row[0] else None

        conn.close()

        if not msgs:
            continue

        display_sid = sid[:35] + '...' if len(sid) > 35 else sid
        print(f"\n[{idx}/{len(sessions)}] 🔍 {display_sid} ({len(msgs)}条)")

        try:
            results = analyzer.analyze_batch(msgs, sid, gap_minutes=15, agent_id=session_agent_id)

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

                    # 使用 sessions 表的实际 session_id（不添加 #1 后缀）
                    r.session_id = sid
                    if save_analysis(r, DB_PATH):
                        print(f"     💾 已保存 → {sid[:40]}...")
                    else:
                        print(f"     ❌ 保存失败（evidence 不合格）")

                success_count += 1
            else:
                print(f"  ⚠️ 无分析结果")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:80]}")
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"🎉 分析完成！成功: {success_count} | 失败: {fail_count} | 总计: {len(sessions)}")
    print(f"{'='*60}")


def find_unanalyzed_sessions(db_path: str = 'data/flow_ecosystem.db', since_minutes: int = 60) -> list:
    """Find sessions with messages but no analysis record."""
    import sqlite3
    from datetime import datetime, timedelta
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    since_time = (datetime.now() - timedelta(minutes=since_minutes)).isoformat()
    c.execute("""
        SELECT DISTINCT s.session_id FROM sessions s
        LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
        WHERE s.timestamp > ? AND sa.session_id IS NULL AND s.role IN ('user', 'assistant') AND (s.is_auto_push = 0 OR s.is_auto_push IS NULL)
        GROUP BY s.session_id HAVING COUNT(*) > 1
    """, (since_time,))
    results = [row[0] for row in c.fetchall()]
    conn.close()
    return results


def _merge_streaming_segments(messages):
    """合并同一 session 内、间隔 <3秒 的连续 assistant 消息"""
    if not messages or len(messages) < 2:
        return messages
    merged = []
    i = 0
    while i < len(messages):
        current = messages[i]
        if current.get('role') == 'assistant' and i + 1 < len(messages):
            next_msg = messages[i + 1]
            if (next_msg.get('role') == 'assistant' and
                next_msg.get('session_id') == current.get('session_id')):
                try:
                    from datetime import datetime
                    t1 = datetime.fromisoformat(str(current['timestamp']).replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(str(next_msg['timestamp']).replace('Z', '+00:00'))
                    if (t2 - t1).total_seconds() < 30.0:
                        current['content_text'] = (
                            (current.get('content_text') or '') + '\n' +
                            (next_msg.get('content_text') or '')
                        ).strip()
                        i += 2
                        merged.append(current)
                        continue
                except Exception:
                    pass
        merged.append(current)
        i += 1
    return merged


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量分析 session 四维指标')
    parser.add_argument('--date', '-d', required=True, help='目标日期 (YYYY-MM-DD)')
    args = parser.parse_args()

    analyze_date(args.date)

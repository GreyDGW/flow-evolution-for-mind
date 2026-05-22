#!/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/.venv/bin/python3
"""完整三层批量会话切割器

基于 PRD V7.5 三层渐进式架构：
- Phase 1: HardRulesLayer（时间/命令/短消息/代码块）
- Phase 2: VectorLayer（语义相似度，ChromaEmbedder）
- Phase 3: LLMArbiterLayer（LLM 模糊地带精判）

输入：sessions 表中未切割的原始 session
输出：UPDATE sessions.session_id（加 # 后缀）

使用方式:
    ./batch_session_cutter.py --date 2026-04-19    # 直接运行（自动使用 .venv）
    python3 batch_session_cutter.py --date 2026-04-19  # 系统Python（可能缺少sentence-transformers）
"""

import os
import sys
import subprocess

# 自动检测并激活项目 .venv（确保 sentence-transformers 可用）
_VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
_VENV_PYTHON = os.path.join(_VENV_DIR, 'bin', 'python3')

def _ensure_venv():
    """确保在 .venv 环境中运行，只在命令行直接调用时触发"""
    # 如果当前 Python 不是 .venv 的 Python，且 .venv 存在，则重新调用
    if os.path.exists(_VENV_PYTHON) and sys.executable != _VENV_PYTHON:
        print(f"🔄 检测到项目 .venv，切换到: {_VENV_PYTHON}")
        # V7.8-9-4-3 FIX: 过滤参数，只传递 cutter 自己认识的参数
        # 防止被 flow_handler.py 的 --intent-type 等参数污染
        import argparse
        _temp_parser = argparse.ArgumentParser()
        _temp_parser.add_argument("--date", default=None)
        _temp_parser.add_argument("--db", default=None)
        _temp_parser.add_argument("session_id", nargs="?")
        _temp_parser.add_argument("--all", action='store_true', default=False)
        _known, _unknown = _temp_parser.parse_known_args(sys.argv[1:])
        _filtered_args = []
        if _known.date:
            _filtered_args.extend(["--date", _known.date])
        if _known.db:
            _filtered_args.extend(["--db", _known.db])
        if _known.session_id:
            _filtered_args.append(_known.session_id)
        if _known.all:
            _filtered_args.append("--all")
        
        result = subprocess.run([_VENV_PYTHON, __file__] + _filtered_args, env=os.environ)
        sys.exit(result.returncode)

print(f"✅ 使用 Python: {sys.executable}")
print(f"✅ 工作目录: {os.getcwd()}")

import sqlite3
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from plugin.session.session_cutter import SessionCutter
from plugin.session_messages import get_session_messages


def _parse_time(ts):
    if isinstance(ts, datetime):
        return ts
    s = str(ts)[:19]
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def batch_cut(session_id: str, db_path: str = 'data/flow_ecosystem.db', embedder=None):
    """对单个 session 执行完整三层批量切割"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. 读取该 session 的所有原始消息（含 rowid，用于最终 UPDATE）
    # V7.8-9-4-3 FIX: 使用 rowid 替代 id（id 字段可能为 NULL 或不唯一）
    c.execute("""
        SELECT rowid, timestamp, content_text, has_code, content_length, role
        FROM sessions
        WHERE session_id = ?
        ORDER BY timestamp
    """, (session_id,))
    all_msgs = [dict(r) for r in c.fetchall()]

    # 2. 复用 session_messages.py 的过滤逻辑获取有效对话消息
    # 过滤空内容 + 合并连续 assistant，返回 {role, content, timestamp}
    dialog_msgs = get_session_messages(session_id, db_path)
    print(f"  📋 原始消息: {len(all_msgs)}条 | 有效对话: {len(dialog_msgs)}条")

    # 3. 清洗 dialog_msgs 的 content（去掉图片标记等）
    import re
    for m in dialog_msgs:
        text = m['content']
        text = re.sub(r'!\[image\][^\s]*', '', text)
        text = re.sub(r'System \(untrusted\):.*?\n', '', text)
        text = re.sub(r'Conversation info.*?\n', '', text)
        m['content'] = text.strip()

    # 4. 用 dialog_msgs 进行切割判定
    msgs = dialog_msgs  # 后续切割逻辑处理 dialog_msgs
    # all_msgs 保留，通过 timestamp 映射回原始消息 id

    if not msgs:
        print(f"⚠️ session {session_id[:20]}... 无消息")
        conn.close()
        return []

    print(f"\n📥 Session {session_id[:20]}... | {len(msgs)} 条消息 | 开始三层切割...")

    if embedder is None:
        try:
            from plugin.session.embedding import create_embedder
            embedder = create_embedder()
            print("  ✅ 嵌入模型已加载（VectorLayer 可用）")
        except Exception as e:
            embedder = None
            print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")
    else:
        print("  ✅ 使用传入的嵌入模型（全局复用）")

    cutter = SessionCutter(llm_client=None, embedder=embedder)

    cut_points = [0]

    for i in range(1, len(msgs)):
        prev = msgs[i - 1]
        curr = msgs[i]

        result = cutter.cut_decision(
            current_turn_content=curr['content'],
            current_turn_time=_parse_time(curr['timestamp']),
            previous_turn_time=_parse_time(prev['timestamp']),
            previous_turn_content=prev['content'],
            session_turn_count=i - cut_points[-1]
        )

        if result.decision.value == 'cut':
            print(f"  🔪 切割点 #{len(cut_points)}: 第{i}条 | {result.layer} | {result.reason}")
            cut_points.append(i)
            cutter.reset_session()

    # 5. 将 dialog_msgs 的切割点通过 timestamp 映射回 all_msgs
    # 切割点定义了 dialog_msgs 的段边界，每段对应一个时间区间
    # 原始消息按时间就近分配到对应子 session
    segments = []
    cut_ts = [msgs[cp]['timestamp'] for cp in cut_points]  # 切割点的时间戳
    cut_ts.append(datetime.max)  # 末尾哨兵

    for idx, (seg_start_ts, seg_end_ts) in enumerate(zip([datetime.min] + cut_ts[:-1], cut_ts)):
        # 找出 all_msgs 中时间落在 [seg_start_ts, seg_end_ts) 的消息
        segment = [
            m for m in all_msgs
            if _parse_time(m['timestamp']) >= _parse_time(seg_start_ts)
            and _parse_time(m['timestamp']) < _parse_time(seg_end_ts)
        ]
        segments.append(segment)

        new_sid = session_id if idx == 0 else f"{session_id}#{idx + 1}"
        
        """
        ⚠️ session_id 字段语义说明（重要！）:
        
        格式: {import_source_id}#{segment_index}
        
        示例:
        - "c8584676..."          → 原始导入组（未切割，idx=0）
        - "c8584676...#2"       → 第2个切割后的对话片段
        - "c8584676...#5"       → 第5个切割后的对话片段
        
        字段命名历史:
        - 物理含义: import_source_id（数据源/文件名标识）
        - 逻辑含义: 切割后近似于 conversation_id（真正的会话标识）
        - 保留原因: 向下兼容，避免大规模 schema 变更
        
        与 semantic_sessions 表的关系:
        - sessions.session_id: 物理分组 + 切割标记（本表）
        - semantic_sessions.id: 独立生成的语义会话ID（可能不同命名空间）
        
        查询建议:
        - 按"文件"聚合: GROUP BY session_id（去掉 # 后缀）
        - 按"对话"聚合: 直接使用 session_id（含 # 后缀）
        """
        ids = [m['rowid'] for m in segment]

        c.executemany(
            "UPDATE sessions SET session_id = ? WHERE rowid = ?",
            [(new_sid, mid) for mid in ids]
        )

        dur = _parse_time(segment[-1]['timestamp']) - _parse_time(segment[0]['timestamp']) if len(segment) > 1 else None
        print(f"    子session {idx + 1}: {new_sid[:30]:30s} | {len(segment):3d}条(对话{len([m for m in segment if m['role'] in ('user','assistant')]):2d}) | 时长{dur}")

    conn.commit()
    conn.close()

    print(f"  ✅ 切割完成: {len(segments)} 个子session")
    return segments


def batch_cut_by_date(target_date: str, db_path: str = 'data/flow_ecosystem.db'):
    """对某一天的全部 session 执行批量切割"""
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    c = conn.cursor()

    # 幂等性：先恢复已切割的 session_id（去掉 # 后缀）
    c.execute("""
        UPDATE sessions
        SET session_id = substr(session_id, 1, instr(session_id, '#') - 1)
        WHERE date(timestamp) = ? AND session_id LIKE '%#%'
    """, (target_date,))
    restored = c.rowcount
    if restored > 0:
        print(f"  🔄 已恢复 {restored} 条记录为原始 session_id")
    conn.commit()

    c.execute("""
        SELECT DISTINCT session_id
        FROM sessions
        WHERE date(timestamp) = ?
    """, (target_date,))
    sessions = [r[0] for r in c.fetchall()]
    conn.close()

    print(f"📅 {target_date} 共 {len(sessions)} 个原始 session 待切割")
    all_segments = []
    # 提前创建 embedder，所有 session 复用（避免重复加载模型）
    from plugin.session.embedding import create_embedder
    try:
        shared_embedder = create_embedder()
        print(f"  ✅ 嵌入模型已全局加载（将被 {len(sessions)} 个 session 复用）")
    except Exception as e:
        shared_embedder = None
        print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")
    
    for sid in sessions:
        segs = batch_cut(sid, db_path, embedder=shared_embedder)
        all_segments.extend(segs)

    total = sum(len(s) for s in all_segments)
    print(f"\n🎉 全部完成: {len(sessions)} 个原始 session → {len(all_segments)} 个子session | 共 {total} 条消息")
    return all_segments


def find_uncut_sessions(db_path: str = 'data/flow_ecosystem.db', since_minutes: int = None) -> list:
    """Find uncut original sessions (no # suffix). If since_minutes is None, scan all history."""
    import sqlite3
    from datetime import datetime, timedelta
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if since_minutes:
        since_time = (datetime.now() - timedelta(minutes=since_minutes)).isoformat()
        time_clause = "AND timestamp > ?"
        params = (since_time,)
    else:
        time_clause = ""
        params = ()

    c.execute(f"""
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id NOT LIKE '%#%' AND role IN ('user', 'assistant') AND (is_auto_push = 0 OR is_auto_push IS NULL) AND (is_system_noise = 0 OR is_system_noise IS NULL) {time_clause}
        GROUP BY session_id HAVING msg_count > 1
    """, params)
    results = [row[0] for row in c.fetchall()]
    conn.close()
    return results


if __name__ == '__main__':
    _ensure_venv()  # V7.8-9-4-3 FIX: 只在命令行直接调用时触发 .venv 切换
    import argparse
    p = argparse.ArgumentParser(description='完整三层批量会话切割器')
    p.add_argument('session_id', nargs='?', help='单个 session_id 切割')
    p.add_argument('--date', help='按日期批量切割 (YYYY-MM-DD)')
    p.add_argument('--all', action='store_true', help='全量切割所有未切割的 session（>1条消息）')
    p.add_argument('--db', default='data/flow_ecosystem.db')
    a = p.parse_args()

    if a.all:
        sessions = find_uncut_sessions(a.db)
        print(f"🔍 发现 {len(sessions)} 个未切割的原始 session")
        
        from plugin.session.embedding import create_embedder
        try:
            shared_embedder = create_embedder()
            print(f"  ✅ 嵌入模型已全局加载（将被 {len(sessions)} 个 session 复用）")
        except Exception as e:
            shared_embedder = None
            print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")
        
        all_segments = []
        for i, sid in enumerate(sessions, 1):
            print(f"\n  [{i}/{len(sessions)}] 切割 {sid}...")
            segs = batch_cut(sid, a.db, embedder=shared_embedder)
            all_segments.extend(segs)
        
        total = sum(len(s) for s in all_segments)
        print(f"\n🎉 全部完成: {len(sessions)} 个原始 session → {len(all_segments)} 个子session | 共 {total} 条消息")
    
    elif a.date:
        batch_cut_by_date(a.date, a.db)
    elif a.session_id:
        batch_cut(a.session_id, a.db)
    else:
        print("用法: python3 batch_session_cutter.py <session_id> [--db path]")
        print("       python3 batch_session_cutter.py --date 2026-04-19 [--db path]")
        print("       python3 batch_session_cutter.py --all [--db path]  # 全量切割")
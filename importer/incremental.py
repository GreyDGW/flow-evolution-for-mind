"""
增量导入模块：从 OpenClaw JSONL 实时/准实时采集数据
基于原 session_collector.py 的成熟逻辑重构
"""
import os
import json
import glob
import sys
import time
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

STATE_FILE = ".collect_state.json"

def load_state(state_path: str = STATE_FILE) -> dict:
    """加载采集状态（每个文件已读取到的位置）"""
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    return {}

def save_state(state: dict, state_path: str = STATE_FILE):
    """保存采集状态"""
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def scan_jsonl_files(base_dir: Optional[str] = None) -> List[str]:
    """递归扫描所有 Agent 的 JSONL 文件（排除备份）

    Args:
        base_dir: 手动指定扫描目录。为 None 时自动发现 OpenClaw 数据目录。
    """
    if base_dir is None:
        # 使用路径发现模块自动定位（跨平台），已包含备份过滤
        try:
            from core.openclaw_path_resolver import get_all_agent_jsonl_files
            files = get_all_agent_jsonl_files()
            return [str(f) for f in files]
        except (RuntimeError, ImportError) as e:
            print(f"⚠️ 自动发现 OpenClaw 目录失败: {e}", file=sys.stderr)
            print("🔄 fallback 到默认路径 ~/.openclaw/agents", file=sys.stderr)
            base_dir = os.path.expanduser("~/.openclaw/agents")
    else:
        base_dir = os.path.expanduser(base_dir)

    pattern = os.path.join(base_dir, "**/*.jsonl")
    files = glob.glob(pattern, recursive=True)
    # 严格过滤：排除 .reset.* 和 .checkpoint.* 备份文件
    return [
        f for f in files
        if os.path.isfile(f)
        and ".reset." not in os.path.basename(f)
        and ".checkpoint." not in os.path.basename(f)
    ]

def read_new_lines(filepath: str, last_position: int = 0) -> tuple[List[str], int]:
    """增量读取文件新增行，返回 (新行列表, 新位置)"""
    new_lines = []
    current_size = os.path.getsize(filepath)
    
    if current_size <= last_position:
        return [], last_position
    
    with open(filepath, 'r', encoding='utf-8') as f:
        f.seek(last_position)
        for line in f:
            line = line.strip()
            if line:
                new_lines.append(line)
        new_position = f.tell()
    
    return new_lines, new_position

def import_batch(lines: List[str], db_path: str, parser_func, source_session_id: str = "") -> int:
    """批量导入一行行 JSONL 到 sessions 表"""
    from importer.base_parser import _parse_jsonl_line, _get_session_id_from_path
    
    inserted = 0
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # V7.8-9-4-3 FIX: 首次导入时自动创建 sessions 表（基于首条记录的字段结构）
    table_created = False
    
    # V7.8-9-4-3 FIX: session → agent_id 映射缓存（解决 message 类型继承问题）
    session_agent_map = {}
    
    for line in lines:
        try:
            record = _parse_jsonl_line(line, source_session_id)
            if not record:
                continue
            
            # V7.8-9-4-3 FIX: message 类型继承 session 的 agent_id
            rec_type = record.get("type", "")
            rec_sid = record.get("session_id", "")
            rec_aid = record.get("agent_id")
            
            if rec_type == "session" and rec_aid:
                # 缓存 session 级别的 agent_id
                session_agent_map[rec_sid] = rec_aid
            elif rec_type in ("message", "custom", "model_change", "thinking_level_change"):
                # 这些类型通常没有自己的 agent_id，从同 session 继承
                if not rec_aid and rec_sid in session_agent_map:
                    record["agent_id"] = session_agent_map[rec_sid]
            
            # V7.8-9-4-6 FIX: 标记系统噪音（扩展版）
            content_text = record.get("content_text") or ""
            role = record.get("role", "")
            
            # 噪音模式库
            NOISE_PATTERNS = {
                'HEARTBEAT_OK', 'NO_REPLY', 'HEARTBEAT', 'PING', 'PONG',
                'ANNOUNCE_SKIP'
            }
            
            is_noise = False
            if not content_text or len(content_text.strip()) == 0:
                # 空内容（主要是 assistant 角色的空响应）
                if role == 'assistant':
                    is_noise = True
                    record['is_auto_push'] = 1
            elif 'Agent-to-agent announce step' in content_text:
                # Agent-to-Agent 通信：不是系统噪音，但是业务中转
                record['is_auto_push'] = 1
                record['is_system_noise'] = 0
            elif content_text in NOISE_PATTERNS or content_text.startswith('[cron:') or content_text.startswith('Read HEARTBEAT.md'):
                is_noise = True
            elif any(p in content_text for p in NOISE_PATTERNS):
                is_noise = True
            elif '] NO_REPLY' in content_text:
                # 带时间戳前缀的 NO_REPLY 变体
                is_noise = True
            
            record["is_system_noise"] = 1 if is_noise else 0

            # === V7.8-9-4-6: 业务级中转检测 ===
            if (role == 'assistant' and len(content_text) < 30 and
                (content_text.startswith('收到') or '已同步' in content_text or '待命' in content_text)):
                record['is_auto_push'] = 1
            elif 'is_auto_push' not in record:
                record['is_auto_push'] = 0
            
            # 首次成功解析记录时，自动创建表（如果不存在）
            if not table_created:
                try:
                    c.execute("SELECT 1 FROM sessions LIMIT 1")
                    table_created = True
                except sqlite3.OperationalError:
                    # 表不存在，根据 record 的字段 + 已知标准字段动态创建
                    # V7.8-9-4-3 FIX: 预定义所有 OpenClaw 已知字段，避免后续记录字段缺失
                    _KNOWN_FIELDS = {
                        'session_id': 'TEXT', 'type': 'TEXT', 'msg_id': 'TEXT', 'parent_id': 'TEXT',
                        'timestamp': 'TEXT', 'hostname': 'TEXT', 'agent_id': 'TEXT', 'sender_id': 'TEXT',
                        'sender_name': 'TEXT', 'role': 'TEXT', 'content': 'TEXT', 'msg_length': 'INTEGER',
                        'has_code': 'INTEGER', 'is_question': 'INTEGER', 'content_text': 'TEXT',
                        'thinking_text': 'TEXT', 'tool_call_text': 'TEXT', 'tool_result_text': 'TEXT',
                        'model': 'TEXT', 'temperature': 'REAL', 'top_p': 'REAL', 'max_tokens': 'INTEGER',
                        'presence_penalty': 'REAL', 'frequency_penalty': 'REAL', 'stop': 'TEXT',
                        'n': 'INTEGER', 'stream': 'INTEGER', 'logprobs': 'INTEGER', 'echo': 'INTEGER',
                        'best_of': 'INTEGER', 'logit_bias': 'TEXT', 'user': 'TEXT', 'session': 'TEXT',
                        'cwd': 'TEXT', 'id': 'TEXT', 'version': 'TEXT'
                    }
                    all_fields = set(record.keys()) | set(_KNOWN_FIELDS.keys())
                    columns = []
                    for field in sorted(all_fields):
                        if field in _KNOWN_FIELDS:
                            col_type = _KNOWN_FIELDS[field]
                        else:
                            value = record.get(field)
                            if isinstance(value, int):
                                col_type = "INTEGER"
                            elif isinstance(value, float):
                                col_type = "REAL"
                            else:
                                col_type = "TEXT"
                        columns.append(f"{field} {col_type}")
                    
                    create_sql = f"CREATE TABLE sessions ({', '.join(columns)})"
                    c.execute(create_sql)
                    conn.commit()
                    print(f"[增量导入] 自动创建 sessions 表（{len(columns)} 个字段）", file=sys.stderr)
                    table_created = True
            
            # V7.8-9-4-3 FIX: 动态处理字段缺失——遇到新字段自动 ALTER TABLE ADD COLUMN
            c.execute("PRAGMA table_info(sessions)")
            existing_fields = {row[1] for row in c.fetchall()}
            record_fields = set(record.keys())
            missing_fields = record_fields - existing_fields
            
            for field in missing_fields:
                value = record[field]
                if isinstance(value, int):
                    col_type = "INTEGER"
                elif isinstance(value, float):
                    col_type = "REAL"
                else:
                    col_type = "TEXT"
                try:
                    c.execute(f"ALTER TABLE sessions ADD COLUMN {field} {col_type}")
                    existing_fields.add(field)
                    print(f"[增量导入] 自动添加字段: {field}", file=sys.stderr)
                except sqlite3.OperationalError as e:
                    print(f"[增量导入] 添加字段 {field} 失败: {e}", file=sys.stderr)
            
            # 只插入表中实际存在的字段，避免字段不匹配报错
            fields = [f for f in record.keys() if f in existing_fields]
            if not fields:
                print(f"[增量导入] 跳过一行: 无有效字段可插入", file=sys.stderr)
                continue
            placeholders = ','.join(['?' for _ in fields])
            sql = f"INSERT OR IGNORE INTO sessions ({','.join(fields)}) VALUES ({placeholders})"
            c.execute(sql, [record[f] for f in fields])
            if c.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"[增量导入] 跳过一行: {e}")
    
    conn.commit()

    # V7.8-9-4-3 FIX: Session 补全机制 - 为缺少 agent_id 的 message 记录从数据库继承
    try:
        # 收集本 batch 中缺少 agent_id 的 session_id
        missing_agent_sessions = set()
        for line in lines:
            try:
                record = _parse_jsonl_line(line, source_session_id)
                if not record:
                    continue
                rec_type = record.get("type", "")
                rec_sid = record.get("session_id", "")
                rec_aid = record.get("agent_id")
                if rec_type in ("message", "custom") and (not rec_aid or rec_aid == "") and rec_sid:
                    missing_agent_sessions.add(rec_sid)
            except:
                pass

        if missing_agent_sessions:
            for sid in missing_agent_sessions:
                c.execute(
                    "SELECT agent_id FROM sessions WHERE session_id = ? AND agent_id IS NOT NULL AND agent_id != '' LIMIT 1",
                    (sid,)
                )
                row = c.fetchone()
                if row and row[0]:
                    c.execute(
                        "UPDATE sessions SET agent_id = ? WHERE session_id = ? AND (agent_id IS NULL OR agent_id = '')",
                        (row[0], sid)
                    )
                    updated = c.rowcount
                    if updated > 0:
                        print(f"[增量导入] Session 补全: {sid} 继承 agent_id={row[0]} ({updated} 条)", file=sys.stderr)
            conn.commit()
    except Exception as e:
        print(f"[增量导入] Session 补全失败: {e}", file=sys.stderr)

    conn.close()
    return inserted

def run_async_collector(
    jsonl_dir: Optional[str] = None,
    db_path: str = "data/flow_ecosystem.db",
    poll_interval: int = 30,
    batch_size: int = 50,
    state_path: str = ".collect_state.json"
):
    """异步轮询采集器：每30秒扫描一次，持续运行"""
    print(f"[异步采集] 启动 | 扫描目录: {jsonl_dir} | 轮询间隔: {poll_interval}s")
    state = load_state(state_path)
    
    try:
        while True:
            files = scan_jsonl_files(jsonl_dir)
            total_inserted = 0
            
            for filepath in files:
                rel_path = os.path.relpath(filepath)
                last_pos = state.get(rel_path, 0)
                
                new_lines, new_pos = read_new_lines(filepath, last_pos)
                if new_lines:
                    from pathlib import Path
                    from importer.base_parser import _get_session_id_from_path
                    sid = _get_session_id_from_path(Path(filepath))
                    inserted = import_batch(new_lines[:batch_size], db_path, None, sid)
                    total_inserted += inserted
                    state[rel_path] = new_pos
                    print(f"  {rel_path}: +{inserted} 条 (位置 {last_pos} -> {new_pos})")
            
            if total_inserted > 0:
                save_state(state, state_path)
                print(f"[异步采集] 本轮共导入 {total_inserted} 条")
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print("\n[异步采集] 用户中断，保存状态...")
        save_state(state, state_path)

def run_once(jsonl_dir: Optional[str] = None, db_path: str = "data/flow_ecosystem.db"):
    """单次增量导入（适合手动触发或定时任务）"""
    state = load_state()
    files = scan_jsonl_files(jsonl_dir)
    total = 0
    
    for filepath in files:
        rel_path = os.path.relpath(filepath)
        last_pos = state.get(rel_path, 0)
        new_lines, new_pos = read_new_lines(filepath, last_pos)
        if new_lines:
            from pathlib import Path
            from importer.base_parser import _get_session_id_from_path
            sid = _get_session_id_from_path(Path(filepath))
            inserted = import_batch(new_lines, db_path, None, sid)
            total += inserted
            state[rel_path] = new_pos
            print(f"  {rel_path}: +{inserted} 条")
    
    save_state(state)
    print(f"[单次采集] 共导入 {total} 条")

    # === AutoCut: after import, detect and cut uncut sessions ===
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # V7.8-9-4-3 FIX: 导入 cutter 前清空 sys.argv，防止参数污染
        _saved_cutter_argv = sys.argv[:]
        sys.argv = [sys.argv[0]]
        try:
            from batch_session_cutter import find_uncut_sessions, batch_cut
        finally:
            sys.argv = _saved_cutter_argv
        uncut = find_uncut_sessions(db_path=db_path, since_minutes=1440)  # 24小时窗口，与 AutoAnalyze 一致
        if uncut:
            print(f"[AutoCut] Found {len(uncut)} uncut sessions, cutting...")
            for sid in uncut:
                try:
                    batch_cut(session_id=sid, db_path=db_path)
                    print(f"[AutoCut] Done {sid}")
                except Exception as e:
                    print(f"[AutoCut] Failed {sid}: {e}")
        else:
            print("[AutoCut] No uncut sessions")
    except Exception as e:
        print(f"[AutoCut] Error: {e}")

    # === AutoAnalyze: after cutting, analyze unanalyzed sessions ===
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from batch_analyze_with_save import find_unanalyzed_sessions, analyze_date
        from datetime import datetime
        unanalyzed = find_unanalyzed_sessions(db_path=db_path, since_minutes=1440)  # 24小时窗口
        if unanalyzed:
            print(f"[AutoAnalyze] Found {len(unanalyzed)} unanalyzed sessions")
            today_str = datetime.now().strftime("%Y-%m-%d")
            try:
                analyze_date(target_date=today_str)
                print(f"[AutoAnalyze] Batch analyze done for {today_str}")
            except Exception as e:
                print(f"[AutoAnalyze] Batch analyze failed: {e}")
        else:
            print("[AutoAnalyze] No unanalyzed sessions")
    except Exception as e:
        print(f"[AutoAnalyze] Error: {e}")

    return total


def _merge_streaming_segments(messages):
    """合并同一session内连续assistant的流式分段（间隔<<30秒）"""
    if not messages:
        return messages
    merged = [messages[0]]
    for curr in messages[1:]:
        prev = merged[-1]
        if (curr.get('role') == 'assistant' and prev.get('role') == 'assistant' 
            and curr.get('session_id') == prev.get('session_id') 
            and curr.get('timestamp') and prev.get('timestamp')):
            try:
                from datetime import datetime
                t1 = datetime.fromisoformat(prev['timestamp'].replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(curr['timestamp'].replace('Z', '+00:00'))
                if 0 <= (t2 - t1).total_seconds() <= 30.0:
                    prev['content_text'] = (prev.get('content_text', '') + '\n' + curr.get('content_text', '')).strip()
                    prev['msg_length'] = prev.get('msg_length', 0) + curr.get('msg_length', 0)
                    continue
            except Exception:
                pass
        merged.append(curr)
    return merged


def merge_streaming_segments_in_db(db_path='data/flow_ecosystem.db'):
    """数据库内后处理：合并已入库的流式分段"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT DISTINCT session_id FROM sessions WHERE role='assistant' AND (is_system_noise=0 OR is_system_noise IS NULL) AND (is_auto_push=0 OR is_auto_push IS NULL)")
    total = 0
    for (sid,) in c.fetchall():
        c.execute("SELECT rowid, role, content_text, timestamp, msg_length FROM sessions WHERE session_id=? AND (is_system_noise=0 OR is_system_noise IS NULL) AND (is_auto_push=0 OR is_auto_push IS NULL) ORDER BY timestamp", (sid,))
        rows = c.fetchall()
        if len(rows) < 2:
            continue
        to_del = []
        i = 0
        while i < len(rows) - 1:
            if rows[i][1] == 'assistant' and rows[i+1][1] == 'assistant':
                from datetime import datetime
                t1 = datetime.fromisoformat(rows[i][3].replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(rows[i+1][3].replace('Z', '+00:00'))
                if 0 <= (t2 - t1).total_seconds() <= 30.0:
                    nt = (rows[i][2] or '') + '\n' + (rows[i+1][2] or '')
                    nl = (rows[i][4] or 0) + (rows[i+1][4] or 0)
                    c.execute("UPDATE sessions SET content_text=?, msg_length=? WHERE rowid=?", (nt.strip(), nl, rows[i][0]))
                    to_del.append(rows[i+1][0])
                    total += 1
                    rows[i] = (rows[i][0], rows[i][1], nt.strip(), rows[i][3], nl)
                    rows.pop(i + 1)
                    continue
            i += 1
        for rid in to_del:
            c.execute("DELETE FROM sessions WHERE rowid=?", (rid,))
    conn.commit()
    conn.close()
    print(f'✅ 数据库内流式合并完成，共合并 {total} 条')

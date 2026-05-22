import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any, Optional

CHINA_TZ = ZoneInfo("Asia/Shanghai")

SESSION_COLUMNS = [
    "session_id", "type", "msg_id", "parent_id", "timestamp", "hostname", "agent_id",
    "sender_id", "sender_name", "role", "model", "api", "provider",
    "input_tokens", "output_tokens", "total_tokens", "total_cost",
    "stop_reason", "tool_name", "tool_input", "tool_use_id",
    "is_error", "is_question", "has_code",
    "content_text", "thinking_text", "tool_call_text", "content_length",
    "media_path", "media_type",
    "custom_type", "custom_data",
    "complete_raw"
]

def _convert_iso_timestamp(iso_timestamp: str, target_tz: ZoneInfo = CHINA_TZ) -> datetime:
    if not iso_timestamp:
        return datetime.now(target_tz)
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        dt = dt.replace(tzinfo=timezone.utc).astimezone(target_tz)
        return dt.replace(tzinfo=None)
    except Exception:
        return datetime.now(target_tz)

def _extract_sender_info(content: Any) -> tuple[Optional[str], Optional[str]]:
    sender_id = None
    sender_name = None
    if isinstance(content, str):
        id_match = re.search(r'"sender_id":\s*"([^"]+)"', content)
        name_match = re.search(r'"sender":\s*"([^"]+)"', content)
        if id_match:
            sender_id = id_match.group(1)
        if name_match:
            raw_name = name_match.group(1)
            if raw_name and len(raw_name) < 100 and not raw_name.startswith("{") and "metadata" not in raw_name.lower():
                sender_name = raw_name
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text = item.get("text", "")
                    id_match = re.search(r'"sender_id":\s*"([^"]+)"', text)
                    name_match = re.search(r'"sender":\s*"([^"]+)"', text)
                    if id_match:
                        sender_id = id_match.group(1)
                    if name_match:
                        raw_name = name_match.group(1)
                        if raw_name and len(raw_name) < 100 and not raw_name.startswith("{") and "metadata" not in raw_name.lower():
                            sender_name = raw_name
    return sender_id, sender_name

def _extract_content_parts(content: Any) -> tuple[str, str, str, str, str]:
    text_content = ""
    thinking_content = ""
    tool_call_text = ""
    media_path = ""
    media_type = ""

    if isinstance(content, str):
        text_content = content
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                if item_type == "text":
                    text = item.get("text", "")
                    text, extracted_path, extracted_type = _clean_media_text(text)
                    text_content += text
                    if extracted_path:
                        media_path = extracted_path
                        media_type = extracted_type
                elif item_type == "thinking":
                    thinking_content += item.get("thinking", "")
                elif item_type == "toolCall":
                    tool_name = item.get("name", "")
                    args = item.get("arguments", {})
                    args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args)
                    tool_call_text += f"[toolCall: {tool_name}] {args_str}\n"
            elif isinstance(item, str):
                text_content += item
    return text_content, thinking_content, tool_call_text, media_path, media_type

def _clean_media_text(text: str) -> tuple[str, str, str]:
    import re
    media_path = ""
    media_type = ""
    
    media_match = re.search(r'\[media attached:\s*([^\]]+)\]', text)
    if media_match:
        media_block = media_match.group(1)
        path_match = re.search(r'([^\s(]+)\.jpg\s*\(([^)]+)\)', media_block)
        if path_match:
            media_path = path_match.group(1) + ".jpg"
            media_type = path_match.group(2)
        
        text = re.sub(r'\[media attached:\s*[^\]]+\]\s*', '', text)
        text = re.sub(r'To send an image back,.*?(?=\nConversation info|\nSender|\n\[message_id|\Z)', '', text, flags=re.DOTALL)
        text = re.sub(r'\[image_key:\s*[^\]]+\]\s*', '', text)
    
    text = re.sub(r'Conversation info \(untrusted metadata\):\s*```json[\s\S]*?```', '', text)
    text = re.sub(r'Sender \(untrusted metadata\):\s*```json[\s\S]*?```', '', text)
    text = re.sub(r'\[message_id:\s*[^\]]+\]\s*', '', text)
    text = re.sub(r'^\s*```json[\s\S]*?```\s*', '', text)
    
    text = re.sub(r'^\[Bootstrap pending\]\s*', '', text)
    text = re.sub(r'Please read BOOTSTRAP\.md from the workspace.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
    
    return text.strip(), media_path, media_type

def _clean_metadata_text(text: str) -> str:
    cleaned = text
    
    import re
    
    cleaned = re.sub(r'Conversation info \(untrusted metadata\):\s*```json[\s\S]*?```', '', cleaned)
    cleaned = re.sub(r'Sender \(untrusted metadata\):\s*```json[\s\S]*?```', '', cleaned)
    cleaned = re.sub(r'\[message_id:\s*[^\]]+\]\s*', '', cleaned)
    cleaned = re.sub(r'^\s*```json[\s\S]*?```\s*', '', cleaned)
    
    lines = cleaned.split('\n')
    result_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('---'):
            continue
        if line.startswith('name:') and ':' in line:
            continue
        if line.startswith('description:'):
            continue
        if line.startswith('version:'):
            continue
        if line.startswith('model:'):
            continue
        if line.startswith('api-key:'):
            continue
        if line.startswith('provider:'):
            continue
        if line.startswith('plugins:'):
            continue
        if line.startswith('contexts:'):
            continue
        if line.startswith('cache:'):
            continue
        if line.startswith('memory:'):
            continue
        if line.startswith('runtime:'):
            continue
        if line.startswith('qna:'):
            continue
        
        match = re.match(r'^[\u4e00-\u9fff]+:\s*(.+)$', line)
        if match:
            result_lines.append(match.group(1))
            continue
        
        if line:
            result_lines.append(line)
    
    return '\n'.join(result_lines).strip()

def _extract_usage(message_obj: dict) -> tuple[int, int, int, float]:
    usage = message_obj.get("usage", {})
    input_tokens = usage.get("input", 0) or usage.get("input_tokens", 0)
    output_tokens = usage.get("output", 0) or usage.get("output_tokens", 0)
    total_tokens = usage.get("total", 0) or usage.get("total_tokens", 0)
    cost_info = usage.get("cost", {})
    total_cost = 0.0
    if isinstance(cost_info, dict):
        total_cost = cost_info.get("total", 0.0) or 0.0
    elif isinstance(cost_info, (int, float)):
        total_cost = float(cost_info)
    return input_tokens, output_tokens, total_tokens, total_cost

def _parse_jsonl_line(line: str, session_id: str, agent_id: str = None) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None

    record_type = record.get("type", "")
    timestamp = _convert_iso_timestamp(record.get("timestamp", ""))

    if record_type == "session":
        cwd = record.get("cwd", "")
        agent_id = None
        if cwd:
            match = re.search(r'/agents/([^/]+)/', cwd)
            if match:
                agent_id = match.group(1)
        return {
            "session_id": session_id,
            "type": "session",
            "msg_id": record.get("id"),
            "parent_id": None,
            "timestamp": timestamp,
            "hostname": cwd,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "system",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": None,
            "tool_input": None,
            "tool_use_id": None,
            "is_error": 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": None,
            "thinking_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    elif record_type == "message":
        message_obj = record.get("message", {})
        role = message_obj.get("role", "unknown")
        content = message_obj.get("content", [])
        text_content, thinking_content, tool_call_text, media_path, media_type = _extract_content_parts(content)
        sender_id, sender_name = _extract_sender_info(content)
        input_tokens, output_tokens, total_tokens, total_cost = _extract_usage(message_obj)
        is_question = 1 if "?" in text_content else 0
        has_code = 1 if "```" in text_content or "code" in text_content.lower() else 0
        
        if role == 'toolResult':
            text_content = None
            thinking_content = None
            content_len = 0
            media_path = None
            media_type = None
        else:
            content_len = len(text_content) if text_content else 0

        return {
            "session_id": session_id,
            "type": "message",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "role": role,
            "model": message_obj.get("model"),
            "api": message_obj.get("api"),
            "provider": message_obj.get("provider"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "stop_reason": message_obj.get("stopReason"),
            "tool_name": None,
            "tool_input": None,
            "tool_use_id": None,
            "is_error": 0,
            "is_question": is_question,
            "has_code": has_code,
            "content_text": text_content,
            "thinking_text": thinking_content if thinking_content else None,
            "tool_call_text": tool_call_text if tool_call_text else None,
            "content_length": content_len,
            "media_path": media_path if media_path else None,
            "media_type": media_type if media_type else None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    elif record_type == "tool_use":
        tool_obj = record.get("toolUse", {})
        return {
            "session_id": session_id,
            "type": "tool_use",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "assistant",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": tool_obj.get("name"),
            "tool_input": json.dumps(tool_obj.get("input", {}), ensure_ascii=False),
            "tool_use_id": tool_obj.get("id"),
            "is_error": 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": tool_obj.get("name"),
            "thinking_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    elif record_type == "tool_result":
        tool_result = record.get("toolResult", {})
        content_ref = tool_result.get("content", [])
        text_content, thinking_content, tool_call_text, _, _ = _extract_content_parts(content_ref)
        return {
            "session_id": session_id,
            "type": "tool_result",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "tool",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": tool_result.get("toolName"),
            "tool_input": None,
            "tool_use_id": tool_result.get("toolUseId"),
            "is_error": 1 if tool_result.get("isError") else 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": None,
            "thinking_text": None,
            "tool_call_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    elif record_type == "custom":
        custom_type_val = record.get("customType", "")
        custom_data_val = record.get("data", {})
        return {
            "session_id": session_id,
            "type": "custom",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "system",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": None,
            "tool_input": None,
            "tool_use_id": None,
            "is_error": 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": None,
            "thinking_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": custom_type_val if custom_type_val else None,
            "custom_data": json.dumps(custom_data_val, ensure_ascii=False) if custom_data_val else None,
            "complete_raw": line
        }

    elif record_type == "model_change":
        return {
            "session_id": session_id,
            "type": "model_change",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "system",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": None,
            "tool_input": None,
            "tool_use_id": None,
            "is_error": 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": None,
            "thinking_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    elif record_type == "thinking_level_change":
        return {
            "session_id": session_id,
            "type": "thinking_level_change",
            "msg_id": record.get("id"),
            "parent_id": record.get("parentId"),
            "timestamp": timestamp,
            "hostname": None,
            "agent_id": agent_id,
            "sender_id": None,
            "sender_name": None,
            "role": "system",
            "model": None,
            "api": None,
            "provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "stop_reason": None,
            "tool_name": None,
            "tool_input": None,
            "tool_use_id": None,
            "is_error": 0,
            "is_question": 0,
            "has_code": 0,
            "content_text": None,
            "thinking_text": None,
            "content_length": 0,
            "media_path": None,
            "media_type": None,
            "custom_type": None,
            "custom_data": None,
            "complete_raw": line
        }

    return None

def _get_session_id_from_path(jsonl_path: Path) -> str:
    return jsonl_path.stem.split(".jsonl")[0].split(".reset")[0]

def _load_collect_state(db_path: Path) -> dict:
    state_file = db_path.parent / ".collect_state.json"
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_collect_state(db_path: Path, state: dict):
    state_file = db_path.parent / ".collect_state.json"
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  保存采集状态失败: {e}")

def _get_file_modified_time(file_path: Path) -> int:
    return int(file_path.stat().st_mtime * 1000)

def _batch_insert(cursor, records: list):
    if not records:
        return
    placeholders = ", ".join(["?"] * len(SESSION_COLUMNS))
    insert_sql = f"""
        INSERT OR IGNORE INTO sessions ({", ".join(SESSION_COLUMNS)})
        VALUES ({placeholders})
    """
    for record in records:
        values = [record.get(col) for col in SESSION_COLUMNS]
        try:
            cursor.execute(insert_sql, values)
        except sqlite3.IntegrityError:
            pass

def collect_session(jsonl_path: Path, db_path: Path, batch_size: int = 50) -> int:
    session_id = _get_session_id_from_path(jsonl_path)
    state = _load_collect_state(db_path)
    file_state = state.get(str(jsonl_path), {})

    last_offset = file_state.get("lastLineOffset", 0)
    last_modified = file_state.get("lastModified", 0)
    current_modified = _get_file_modified_time(jsonl_path)

    if last_modified == current_modified and last_offset > 0:
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    records = []
    lines_skipped = 0

    agent_id = None

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num <= last_offset:
                lines_skipped += 1
                continue

            record = _parse_jsonl_line(line, session_id, agent_id)
            if record:
                if record.get("agent_id") and not agent_id:
                    agent_id = record.get("agent_id")
                records.append(record)

            if len(records) >= batch_size:
                _batch_insert(cursor, records)
                conn.commit()
                records = []

    if records:
        _batch_insert(cursor, records)
        conn.commit()

    new_offset = last_offset + (len(records) + lines_skipped)
    state[str(jsonl_path)] = {
        "lastLineOffset": new_offset,
        "lastModified": current_modified
    }
    _save_collect_state(db_path, state)

    conn.close()
    return len(records)

def collect_all_sessions(jsonl_dir: Path, db_path: Path, batch_size: int = 50) -> int:
    jsonl_files = list(jsonl_dir.glob("*.jsonl*"))
    total_collected = 0
    for jsonl_file in jsonl_files:
        count = collect_session(jsonl_file, db_path, batch_size)
        total_collected += count
    return total_collected

def import_jsonl_file(jsonl_path: Path, db_path: Path) -> int:
    session_id = _get_session_id_from_path(jsonl_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = _parse_jsonl_line(line, session_id)
            if record:
                records.append(record)

    if records:
        _batch_insert(cursor, records)
        conn.commit()

    conn.close()
    return len(records)

def run_async_collector(jsonl_dir: Path, db_path: Path, 
                        poll_interval: int = 30, batch_size: int = 50):
    """
    异步采集器 - 持续监控并采集新数据
    
    参数:
        jsonl_dir: JSONL文件目录
        db_path: 数据库路径
        poll_interval: 轮询间隔（秒），默认30秒
        batch_size: 批量大小
    """
    print(f"🔄 启动异步采集器")
    print(f"📂 监控目录: {jsonl_dir}")
    print(f"💾 数据库: {db_path}")
    print(f"⏱️  轮询间隔: {poll_interval}秒")
    print("-" * 60)

    try:
        while True:
            count = collect_all_sessions(jsonl_dir, db_path, batch_size)
            if count > 0:
                print(f"� [{datetime.now().strftime('%H:%M:%S')}] 新增记录: {count} 条")
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n� 采集器已停止")

def run_session_end_collector(jsonl_dir: Path, db_path: Path, 
                              session_timeout: int = 300, batch_size: int = 50):
    """
    会话结束触发采集器 - 检测会话空闲后触发采集
    
    逻辑：
    1. 持续监控 JSONL 文件的修改时间
    2. 当文件在 session_timeout 秒内没有更新，认为会话已结束
    3. 触发数据采集并更新采集状态
    4. 避免重复采集（同一会话只采集一次，直到有新数据）
    
    参数:
        jsonl_dir: JSONL文件目录
        db_path: 数据库路径
        session_timeout: 会话超时时间（秒），默认5分钟
        batch_size: 批量大小
    """
    print(f"🔄 启动会话结束采集器")
    print(f"📂 监控目录: {jsonl_dir}")
    print(f"💾 数据库: {db_path}")
    print(f"⏱️  会话超时: {session_timeout}秒（会话空闲此时间后触发采集）")
    print("-" * 60)

    last_collect_time = {}
    last_file_modified = {}
    
    try:
        while True:
            jsonl_files = list(jsonl_dir.glob("*.jsonl*"))
            
            for jsonl_file in jsonl_files:
                session_id = _get_session_id_from_path(jsonl_file)
                current_modified = _get_file_modified_time(jsonl_file)
                
                if session_id not in last_file_modified:
                    last_file_modified[session_id] = 0
                    last_collect_time[session_id] = 0
                
                file_changed = current_modified > last_file_modified[session_id]
                
                if file_changed:
                    last_file_modified[session_id] = current_modified
                    print(f"📝 检测到会话 {session_id[:8]}... 有新数据")
                    continue
                
                time_since_modified = (time.time() * 1000 - current_modified) / 1000
                
                if time_since_modified >= session_timeout:
                    last_collect_time_val = last_collect_time.get(session_id, 0)
                    
                    if current_modified > last_collect_time_val:
                        print(f"📥 [{datetime.now().strftime('%H:%M:%S')}] 会话 {session_id[:8]}... 已空闲 {int(time_since_modified)}秒，触发采集")
                        count = collect_session(jsonl_file, db_path, batch_size)
                        if count > 0:
                            print(f"  ✅ 新增记录: {count} 条")
                        else:
                            print(f"  ⏭️  无新数据")
                        last_collect_time[session_id] = current_modified
            
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 采集器已停止")

if __name__ == "__main__":
    import sys
    from pathlib import Path

    base_path = Path("/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin")
    jsonl_dir = base_path / "tests" / "data"
    db_path = base_path / "flow_ecosystem.db"

    batch_size = 50
    full_mode = False
    async_mode = False
    session_end_mode = False
    target_file = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--full":
            full_mode = True
        elif args[i] == "--batch":
            if i + 1 < len(args):
                batch_size = int(args[i + 1])
                i += 1
        elif args[i] == "--async":
            async_mode = True
        elif args[i] == "--session-end":
            session_end_mode = True
        elif args[i] == "--help":
            print("""
用法: python session_collector.py [选项]

选项:
  --full          完整重新导入（清除现有数据）
  --batch N       设置批量大小（默认 50）
  --async         启动异步轮询采集器（每30秒检查）
  --session-end   启动会话结束采集器（空闲5分钟后触发）
  --help          显示此帮助信息
  <文件路径>      导入单个 JSONL 文件

示例:
  python session_collector.py              # 单次采集
  python session_collector.py --full        # 完整重新导入
  python session_collector.py --async       # 异步轮询模式
  python session_collector.py --session-end # 会话结束触发模式
            """)
            sys.exit(0)
        else:
            target_file = Path(args[i])
        i += 1

    if full_mode:
        print("🔄 完整重新导入模式\n")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions")
        conn.commit()
        conn.close()

        state_file = base_path / ".collect_state.json"
        if state_file.exists():
            state_file.unlink()

    if async_mode:
        run_async_collector(jsonl_dir, db_path, batch_size=batch_size)
    elif session_end_mode:
        run_session_end_collector(jsonl_dir, db_path, batch_size=batch_size)
    elif target_file and target_file.exists():
        count = import_jsonl_file(target_file, db_path)
        print(f"✅ 导入 {target_file.name}: {count} 条记录")
    else:
        print(f"⚙️ 批量大小: {batch_size}")
        count = collect_all_sessions(jsonl_dir, db_path, batch_size)
        print(f"🎉 采集完成！共新增 {count} 条记录")
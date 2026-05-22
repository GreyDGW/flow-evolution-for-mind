import json
import sqlite3
from datetime import datetime
from pathlib import Path

def parse_timestamp(ts):
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return datetime.now()
    return datetime.now()

def import_jsonl_to_db(jsonl_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sessions_data = []
    messages_data = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                record_type = record.get('type', '')
                timestamp = parse_timestamp(record.get('timestamp', datetime.now().isoformat()))

                if record_type == 'session':
                    sessions_data.append({
                        'session_id': record.get('id', ''),
                        'timestamp': timestamp,
                        'role': 'system',
                        'content': json.dumps(record, ensure_ascii=False),
                        'msg_length': len(line),
                        'has_code': 0,
                        'is_question': 0,
                        'concept_density': 0.0,
                        'topic_vector_id': None
                    })

                elif record_type == 'message':
                    msg = record.get('message', {})
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', [])

                    text_content = ''
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '')
                                elif item.get('type') == 'thinking':
                                    text_content += f"[思考: {item.get('thinking', '')}]"
                            elif isinstance(item, str):
                                text_content += item
                    elif isinstance(content, str):
                        text_content = content

                    messages_data.append({
                        'session_id': record.get('id', ''),
                        'timestamp': timestamp,
                        'role': role,
                        'content': text_content if text_content else '',
                        'msg_length': len(text_content),
                        'has_code': 1 if '```' in text_content or 'code' in text_content.lower() else 0,
                        'is_question': 1 if '?' in text_content else 0,
                        'concept_density': 0.5,
                        'topic_vector_id': record.get('id', '')
                    })

            except json.JSONDecodeError as e:
                print(f"跳过第 {line_num} 行: JSON解析错误 - {e}")
                continue
            except Exception as e:
                print(f"跳过第 {line_num} 行: {e}")
                continue

    for data in sessions_data:
        try:
            cursor.execute('''
                INSERT INTO sessions (session_id, timestamp, role, content, msg_length, has_code, is_question, concept_density, topic_vector_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['session_id'], data['timestamp'], data['role'], data['content'],
                  data['msg_length'], data['has_code'], data['is_question'],
                  data['concept_density'], data['topic_vector_id']))
        except sqlite3.IntegrityError:
            pass

    for data in messages_data:
        try:
            cursor.execute('''
                INSERT INTO sessions (session_id, timestamp, role, content, msg_length, has_code, is_question, concept_density, topic_vector_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['session_id'], data['timestamp'], data['role'], data['content'],
                  data['msg_length'], data['has_code'], data['is_question'],
                  data['concept_density'], data['topic_vector_id']))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

    print(f"✅ 导入完成: {jsonl_path}")
    print(f"   - 会话记录: {len(sessions_data)} 条")
    print(f"   - 消息记录: {len(messages_data)} 条")

if __name__ == "__main__":
    base_path = Path("/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin")
    jsonl_files = list((base_path / "tests/data").glob("*.jsonl*"))

    db_path = base_path / "flow_ecosystem.db"

    print(f"找到 {len(jsonl_files)} 个 JSONL 文件")
    print(f"数据库路径: {db_path}")
    print("-" * 50)

    for jsonl_file in jsonl_files:
        print(f"\n正在导入: {jsonl_file.name}")
        import_jsonl_to_db(jsonl_file, db_path)

    print("\n" + "=" * 50)
    print("🎉 所有数据导入完成！")
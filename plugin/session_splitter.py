"""Session 时间切割器：按消息间隔 >15 分钟拆分超长 session"""

from datetime import datetime
from typing import List, Dict, Any


def split_messages_by_time(messages: List[Dict[str, Any]], gap_minutes: int = 15) -> List[List[Dict[str, Any]]]:
    """按时间间隔切割消息为多个子 session"""
    if not messages:
        return []

    sorted_msgs = sorted(messages, key=lambda m: m.get('timestamp', ''))
    chunks = []
    current_chunk = [sorted_msgs[0]]

    for i in range(1, len(sorted_msgs)):
        prev_time = sorted_msgs[i - 1].get('timestamp', '')
        curr_time = sorted_msgs[i].get('timestamp', '')
        if not prev_time or not curr_time:
            current_chunk.append(sorted_msgs[i])
            continue

        try:
            fmt = '%Y-%m-%d %H:%M:%S.%f' if '.' in str(prev_time) else '%Y-%m-%d %H:%M:%S'
            t1 = datetime.strptime(str(prev_time)[:26], fmt)
            t2 = datetime.strptime(str(curr_time)[:26], fmt)
            gap = (t2 - t1).total_seconds() / 60.0
        except Exception:
            gap = 0

        if gap > gap_minutes:
            chunks.append(current_chunk)
            current_chunk = [sorted_msgs[i]]
        else:
            current_chunk.append(sorted_msgs[i])

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_sub_session_id(parent_id: str, index: int) -> str:
    """生成子 session ID：原ID#1、原ID#2"""
    return f"{parent_id}#{index}"
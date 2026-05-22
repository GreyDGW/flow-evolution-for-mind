#!/usr/bin/env python3
"""
Flow Ecosystem V7.3 层级识别引擎
实现三层级的自动识别：
1. turns：配对 user 与 assistant 消息
2. interactions：LLM 判断 turn 之间的语义关联
3. semantic_sessions：LLM 判断 interaction 之间的主题连贯性
"""

import sqlite3
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

DB_PATH = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

try:
    from src.openclaw_flow_plugin.core.llm_manager import LLMManager
except ImportError:
    try:
        from openclaw_flow_plugin.core.llm_manager import LLMManager
    except ImportError:
        LLMManager = None


class TurnIdentifier:
    """识别 turns（单次问答对）"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()

    def identify_all_turns(self):
        """识别所有 turns：将 user 消息与 assistant 回复配对"""
        print("\n🔍 步骤 1: 识别 turns...")

        self.cursor.execute("""
            SELECT id, role, content_text, timestamp, agent_id
            FROM sessions
            WHERE is_valid_for_analysis = 1
            AND role IN ('user', 'assistant')
            ORDER BY timestamp
        """)

        messages = self.cursor.fetchall()
        turns_created = 0

        current_turn = None
        user_in_turn = False

        for msg_id, role, content, timestamp, agent_id in messages:
            if role == 'user':
                if user_in_turn and current_turn:
                    pass

                current_turn = {
                    'user_id': msg_id,
                    'user_content': content,
                    'user_timestamp': timestamp,
                    'user_agent': agent_id,
                    'assistant_id': None,
                    'assistant_content': None,
                    'assistant_timestamp': None,
                    'assistant_agent': None
                }
                user_in_turn = True

            elif role == 'assistant' and user_in_turn and current_turn:
                current_turn['assistant_id'] = msg_id
                current_turn['assistant_content'] = content
                current_turn['assistant_timestamp'] = timestamp
                current_turn['assistant_agent'] = agent_id

                turn_id = str(uuid.uuid4())
                self._create_turn(turn_id, current_turn)
                turns_created += 1

                current_turn = None
                user_in_turn = False

        self.conn.commit()
        print(f"  ✅ 已创建 {turns_created} 个 turns")
        return turns_created

    def _create_turn(self, turn_id: str, turn_data: Dict):
        """创建 turn 记录"""
        self.cursor.execute("""
            INSERT INTO turns (id, start_time, end_time, user_message, assistant_response,
                             message_count, has_goal, goal_text, pdca_stages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            turn_id,
            turn_data['user_timestamp'],
            turn_data['assistant_timestamp'],
            turn_data['user_content'],
            turn_data['assistant_content'],
            2,
            0, None, None
        ))

        self.cursor.execute("""
            UPDATE sessions SET turn_id = ? WHERE id IN (?, ?)
        """, (turn_id, turn_data['user_id'], turn_data['assistant_id']))


class InteractionIdentifier:
    """识别 interactions（语义相关的 turn 组）"""

    def __init__(self, conn: sqlite3.Connection, use_llm: bool = True):
        self.conn = conn
        self.cursor = conn.cursor()
        self.use_llm = use_llm and LLMManager is not None
        if self.use_llm:
            self.llm = LLMManager(provider="minimax")
        else:
            print("  ⚠️ LLM 未启用，使用规则匹配")

    def identify_all_interactions(self):
        """识别所有 interactions"""
        print("\n🔍 步骤 2: 识别 interactions...")

        self.cursor.execute("""
            SELECT id, user_message, start_time
            FROM turns
            ORDER BY start_time
        """)

        turns = self.cursor.fetchall()
        if not turns:
            print("  ⚠️ 没有找到 turns")
            return 0

        interactions_created = 0
        current_interaction = []
        current_interaction_id = str(uuid.uuid4())

        for turn_id, user_msg, start_time in turns:
            if not current_interaction:
                current_interaction_id = str(uuid.uuid4())
                current_interaction = [turn_id]
            else:
                should_add = self._should_add_to_interaction(
                    current_interaction, turn_id, user_msg
                )

                if should_add:
                    current_interaction.append(turn_id)
                else:
                    self._create_interaction(current_interaction_id, current_interaction)
                    interactions_created += 1

                    current_interaction_id = str(uuid.uuid4())
                    current_interaction = [turn_id]

        if current_interaction:
            self._create_interaction(current_interaction_id, current_interaction)
            interactions_created += 1

        self.conn.commit()
        print(f"  ✅ 已创建 {interactions_created} 个 interactions")
        return interactions_created

    def _should_add_to_interaction(self, current_turn_ids: List[str],
                                   new_turn_id: str, new_msg: str) -> bool:
        """判断是否应该将 turn 加入当前 interaction"""
        if not current_turn_ids:
            return True

        if not self.use_llm:
            return self._rule_based_match(current_turn_ids, new_turn_id, new_msg)

        return self._llm_based_match(current_turn_ids, new_turn_id, new_msg)

    def _rule_based_match(self, current_turn_ids: List[str], new_turn_id: str, new_msg: str) -> bool:
        """基于规则的匹配"""
        time_gap_threshold = 30

        self.cursor.execute("""
            SELECT start_time FROM turns WHERE id = ?
        """, (current_turn_ids[-1],))
        last_time = self.cursor.fetchone()[0]
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace(' ', 'T')).timestamp()

        self.cursor.execute("""
            SELECT start_time FROM turns WHERE id = ?
        """, (new_turn_id,))
        new_time = self.cursor.fetchone()[0]
        if isinstance(new_time, str):
            new_time = datetime.fromisoformat(new_time.replace(' ', 'T')).timestamp()

        time_gap = (new_time - last_time) / 60
        if time_gap > time_gap_threshold:
            return False

        self.cursor.execute("""
            SELECT user_message FROM turns WHERE id = ?
        """, (current_turn_ids[-1],))
        last_msg = self.cursor.fetchone()[0]

        if last_msg and new_msg:
            last_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', last_msg.lower()))
            new_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', new_msg.lower()))
            overlap = len(last_words & new_words)
            return overlap >= 2

        return False

    def _llm_based_match(self, current_turn_ids: List[str],
                        new_turn_id: str, new_msg: str) -> bool:
        """基于 LLM 的语义匹配"""
        context_msgs = []
        for tid in current_turn_ids[-3:]:
            self.cursor.execute("SELECT user_message, start_time FROM turns WHERE id = ?", (tid,))
            result = self.cursor.fetchone()
            if result:
                context_msgs.append(f"[Turn] {result[0][:100]}")

        context = "\n".join(context_msgs[-3:])

        prompt = f"""
判断以下新消息是否与之前的对话属于同一语义会话（interaction）：

【之前的对话】
{context}

【新消息】
{new_msg[:200]}

判断规则：
1. 新消息是否继续同一主题？
2. 新消息是否是之前目标的延续？
3. 新消息是否完全不相关的新主题？

请只回答 "是" 或 "否"，不要其他内容。
"""

        try:
            response = self.llm.generate(prompt, max_tokens=50)
            response = response.strip().lower()
            return '是' in response or 'yes' in response or 'true' in response
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}，使用规则匹配")
            return self._rule_based_match(current_turn_ids, new_msg)

    def _create_interaction(self, interaction_id: str, turn_ids: List[str]):
        """创建 interaction 记录"""
        self.cursor.execute("""
            SELECT MIN(start_time), MAX(start_time), COUNT(*)
            FROM turns WHERE id IN ({})
        """.format(','.join('?' * len(turn_ids))), turn_ids)

        min_time, max_time, count = self.cursor.fetchone()

        if isinstance(min_time, str):
            min_time_ts = datetime.fromisoformat(min_time.replace(' ', 'T')).timestamp()
        else:
            min_time_ts = min_time

        if isinstance(max_time, str):
            max_time_ts = datetime.fromisoformat(max_time.replace(' ', 'T')).timestamp()
        else:
            max_time_ts = max_time

        duration = (max_time_ts - min_time_ts) / 60 if min_time and max_time else 0

        topic = self._extract_topic(turn_ids)

        self.cursor.execute("""
            INSERT INTO interactions (id, start_time, end_time, duration_minutes, turn_count, topic_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (interaction_id, min_time, max_time, duration, count, topic))

        self.cursor.execute("""
            UPDATE turns SET interaction_id = ? WHERE id IN ({})
        """.format(','.join('?' * len(turn_ids))), turn_ids + [interaction_id])

        self.cursor.execute("""
            UPDATE sessions SET interaction_id = ?
            WHERE turn_id IN ({})
        """.format(','.join('?' * len(turn_ids))), turn_ids + [interaction_id])

    def _extract_topic(self, turn_ids: List[str]) -> str:
        """提取 interaction 的主题"""
        self.cursor.execute("""
            SELECT user_message FROM turns WHERE id IN ({})
            ORDER BY start_time LIMIT 3
        """.format(','.join('?' * len(turn_ids))), turn_ids)

        msgs = [r[0] for r in self.cursor.fetchall() if r[0]]
        if not msgs:
            return "未知主题"

        topic = msgs[0][:50]
        if len(msgs[0]) > 50:
            topic += "..."

        return topic


class SemanticSessionIdentifier:
    """识别 semantic_sessions（主题会话，可能跨多天）"""

    def __init__(self, conn: sqlite3.Connection, use_llm: bool = True):
        self.conn = conn
        self.cursor = conn.cursor()
        self.use_llm = use_llm and LLMManager is not None
        if self.use_llm:
            self.llm = LLMManager(provider="minimax")
        else:
            print("  ⚠️ LLM 未启用，使用规则匹配")

    def identify_all_semantic_sessions(self):
        """识别所有 semantic_sessions"""
        print("\n🔍 步骤 3: 识别 semantic_sessions...")

        self.cursor.execute("""
            SELECT id, topic_summary, start_time
            FROM interactions
            ORDER BY start_time
        """)

        interactions = self.cursor.fetchall()
        if not interactions:
            print("  ⚠️ 没有找到 interactions")
            return 0

        sessions_created = 0
        current_session_interactions = []
        current_session_id = str(uuid.uuid4())

        for int_id, topic, start_time in interactions:
            if not current_session_interactions:
                current_session_id = str(uuid.uuid4())
                current_session_interactions = [int_id]
            else:
                should_add = self._should_add_to_session(
                    current_session_interactions, int_id, topic
                )

                if should_add:
                    current_session_interactions.append(int_id)
                else:
                    self._create_semantic_session(current_session_id, current_session_interactions)
                    sessions_created += 1

                    current_session_id = str(uuid.uuid4())
                    current_session_interactions = [int_id]

        if current_session_interactions:
            self._create_semantic_session(current_session_id, current_session_interactions)
            sessions_created += 1

        self.conn.commit()
        print(f"  ✅ 已创建 {sessions_created} 个 semantic_sessions")
        return sessions_created

    def _should_add_to_session(self, current_int_ids: List[str],
                               new_int_id: str, new_topic: str) -> bool:
        """判断是否应该将 interaction 加入当前 semantic_session"""
        if not current_int_ids:
            return True

        if not self.use_llm:
            return self._rule_based_session_match(current_int_ids, new_int_id, new_topic)

        return self._llm_based_session_match(current_int_ids, new_int_id, new_topic)

    def _rule_based_session_match(self, current_int_ids: List[str],
                                  new_int_id: str, new_topic: str) -> bool:
        """基于规则的 session 匹配"""
        self.cursor.execute("""
            SELECT MAX(end_time) FROM interactions WHERE id = ?
        """, (current_int_ids[-1],))
        last_time = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT start_time FROM interactions WHERE id = ?
        """, (new_int_id,))
        new_time = self.cursor.fetchone()[0]

        if last_time and new_time:
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time.replace(' ', 'T')).timestamp()
            if isinstance(new_time, str):
                new_time = datetime.fromisoformat(new_time.replace(' ', 'T')).timestamp()
            time_gap = (new_time - last_time) / 3600
            if time_gap > 48:
                return False

        self.cursor.execute("""
            SELECT topic_summary FROM interactions WHERE id = ?
        """, (current_int_ids[-1],))
        last_topic = self.cursor.fetchone()[0] or ""

        if last_topic and new_topic:
            last_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', last_topic.lower()))
            new_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', new_topic.lower()))
            overlap = len(last_words & new_words)
            return overlap >= 3

        return False

    def _llm_based_session_match(self, current_int_ids: List[str],
                                 new_int_id: str, new_topic: str) -> bool:
        """基于 LLM 的 session 语义匹配"""
        context_ints = []
        for iid in current_int_ids[-2:]:
            self.cursor.execute("SELECT topic_summary FROM interactions WHERE id = ?", (iid,))
            result = self.cursor.fetchone()
            if result:
                context_ints.append(f"[Interaction] 主题: {result[0][:80]}")

        context = "\n".join(context_ints)

        prompt = f"""
判断以下新的 interaction 是否与之前的 semantic_session 属于同一主题会话：

【之前的会话主题】
{context}

【新 interaction】
主题: {new_topic[:100]}

判断规则：
1. 是否继续同一项目/主题？
2. 是否是完全独立的新会话？

请只回答 "继续" 或 "新会话"，不要其他内容。
"""

        try:
            response = self.llm.generate(prompt, max_tokens=50)
            response = response.strip()
            return '继续' in response
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}，使用规则匹配")
            return self._rule_based_session_match(current_int_ids, new_int_id, new_topic)

    def _create_semantic_session(self, session_id: str, int_ids: List[str]):
        """创建 semantic_session 记录"""
        self.cursor.execute("""
            SELECT MIN(start_time), MAX(end_time), SUM(turn_count), COUNT(*)
            FROM interactions WHERE id IN ({})
        """.format(','.join('?' * len(int_ids))), int_ids)

        min_time, max_time, total_turns, int_count = self.cursor.fetchone()

        if isinstance(min_time, str):
            min_time_ts = datetime.fromisoformat(min_time.replace(' ', 'T')).timestamp()
        else:
            min_time_ts = min_time or 0

        if isinstance(max_time, str):
            max_time_ts = datetime.fromisoformat(max_time.replace(' ', 'T')).timestamp()
        else:
            max_time_ts = max_time or 0

        duration = (max_time_ts - min_time_ts) / 3600 if min_time and max_time else 0

        self.cursor.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE interaction_id IN ({})
        """.format(','.join('?' * len(int_ids))), int_ids)

        msg_count = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT topic_summary FROM interactions WHERE id = ?
        """, (int_ids[0],))
        title_row = self.cursor.fetchone()
        title = title_row[0] if title_row and title_row[0] else "未命名会话"

        self.cursor.execute("""
            INSERT INTO semantic_sessions
            (id, title, start_time, end_time, duration_minutes, interaction_count, total_message_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, title[:100], min_time, max_time, duration, int_count, msg_count, 'active'))

        self.cursor.execute("""
            UPDATE interactions SET id = id
            WHERE id IN ({})
        """.format(','.join('?' * len(int_ids))), int_ids)

        for int_id in int_ids:
            self.cursor.execute("SELECT id FROM turns WHERE interaction_id = ?", (int_id,))
            turn_ids = [r[0] for r in self.cursor.fetchall() if r[0]]

            if turn_ids:
                placeholders = ','.join('?' * len(turn_ids))
                self.cursor.execute(f"""
                    UPDATE sessions SET semantic_session_id = ? WHERE turn_id IN ({placeholders})
                """, [session_id] + turn_ids)


def run_hierarchy_identification():
    """执行完整的三层级识别"""
    print("\n" + "="*70)
    print("Flow Ecosystem V7.3 层级识别引擎")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)

    try:
        turn_identifier = TurnIdentifier(conn)
        turns_count = turn_identifier.identify_all_turns()

        interaction_identifier = InteractionIdentifier(conn, use_llm=False)
        interactions_count = interaction_identifier.identify_all_interactions()

        session_identifier = SemanticSessionIdentifier(conn, use_llm=False)
        sessions_count = session_identifier.identify_all_semantic_sessions()

        print("\n" + "="*70)
        print("识别完成汇总")
        print("="*70)
        print(f"  📊 turns: {turns_count}")
        print(f"  📊 interactions: {interactions_count}")
        print(f"  📊 semantic_sessions: {sessions_count}")

    except Exception as e:
        print(f"\n❌ 识别失败: {e}")
        raise
    finally:
        conn.close()


def verify_results():
    """验证识别结果"""
    print("\n" + "="*70)
    print("验证识别结果")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n📊 表记录数:")
    for table in ['sessions', 'turns', 'interactions', 'semantic_sessions']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")

    print("\n📋 样本数据:")

    cursor.execute("SELECT id, user_message, assistant_response FROM turns LIMIT 2")
    turns = cursor.fetchall()
    print("\n【Turns 样本】")
    for tid, user, assistant in turns:
        print(f"  Turn: {tid[:20]}...")
        print(f"    User: {user[:60] if user else 'N/A'}...")
        print(f"    Assistant: {assistant[:60] if assistant else 'N/A'}...")

    cursor.execute("SELECT id, topic_summary, turn_count FROM interactions LIMIT 2")
    ints = cursor.fetchall()
    print("\n【Interactions 样本】")
    for iid, topic, count in ints:
        print(f"  Interaction: {iid[:20]}...")
        print(f"    Topic: {topic}")
        print(f"    Turns: {count}")

    cursor.execute("SELECT id, title, interaction_count FROM semantic_sessions LIMIT 2")
    sess = cursor.fetchall()
    print("\n【Semantic Sessions 样本】")
    for sid, title, count in sess:
        print(f"  Session: {sid[:20]}...")
        print(f"    Title: {title}")
        print(f"    Interactions: {count}")

    conn.close()


if __name__ == '__main__':
    run_hierarchy_identification()
    verify_results()
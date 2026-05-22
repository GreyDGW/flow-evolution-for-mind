#!/usr/bin/env python3
"""
Flow Ecosystem V7.3 LLM 驱动的层级识别引擎
实现三层级的自动识别：
1. turns：配对 user 与 assistant 消息
2. interactions：LLM 判断 turn 之间的语义关联
3. semantic_sessions：LLM 判断 interaction 之间的主题连贯性
"""

import sqlite3
import json
import uuid
import re
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

DB_PATH = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin')

try:
    from src.openclaw_flow_plugin.core.llm_manager import LLMManager
except ImportError:
    try:
        from openclaw_flow_plugin.core.llm_manager import LLMManager
    except ImportError:
        LLMManager = None


class LLMDrivenSemanticMatcher:
    """LLM 驱动的语义匹配器"""

    def __init__(self):
        self.llm = None
        self.use_llm = False
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM"""
        if LLMManager is None:
            print("  ⚠️ LLMManager 未找到")
            return

        api_key = os.environ.get("MINIMAX_API_KEY", "")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")

        if not api_key:
            print("  ⚠️ 未设置 API Key")
            return

        try:
            self.llm = LLMManager(provider="minimax")
            self.use_llm = True
            print("  ✅ LLM 语义匹配已启用")
        except Exception as e:
            print(f"  ⚠️ LLM 初始化失败: {e}")
            self.use_llm = False

    def match_turn_to_interaction(self, current_context: List[str], new_turn: Dict) -> Tuple[bool, str]:
        """判断 turn 是否应该加入当前 interaction"""
        if not self.use_llm or not self.llm:
            return self._rule_based_turn_match(current_context, new_turn)

        context_text = "\n".join([
            f"[Turn {i+1}] {ctx[:100]}"
            for i, ctx in enumerate(current_context[-2:])
        ])

        prompt = f"""判断以下新的对话轮次是否与之前的对话属于同一语义会话。

之前的上下文：
{context_text}

新消息：{new_turn.get('user_message', '')[:100]}

判断：新消息是否继续同一主题？
答案格式（只回答 1 或 0）：
1 = 继续同一会话
0 = 新会话
"""

        try:
            response = self.llm.generate(prompt, max_tokens=10)
            response = response.strip().lower()

            if '1' in response or 'true' in response or '是' in response:
                return True, "LLM判断"
            else:
                return False, "LLM判断"
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}")
            return self._rule_based_turn_match(current_context, new_turn)

    def match_interaction_to_session(self, current_context: List[Dict], new_interaction: Dict) -> Tuple[bool, str]:
        """判断 interaction 是否应该加入当前 semantic_session"""
        if not self.use_llm or not self.llm:
            return self._rule_based_session_match(current_context, new_interaction)

        context_text = "\n".join([
            f"[Interaction {i+1}] {ctx.get('topic', '')[:80]}"
            for i, ctx in enumerate(current_context[-2:])
        ])

        prompt = f"""判断以下新的 interaction 是否与之前的会话属于同一主题。

之前的上下文：
{context_text}

新主题：{new_interaction.get('topic', '')[:100]}

判断：是否继续同一会话？
答案格式（只回答 1 或 0）：
1 = 继续同一会话
0 = 新会话
"""

        try:
            response = self.llm.generate(prompt, max_tokens=10)
            response = response.strip().lower()

            if '1' in response or 'true' in response or '是' in response:
                return True, "LLM判断"
            else:
                return False, "LLM判断"
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}")
            return self._rule_based_session_match(current_context, new_interaction)

    def _rule_based_turn_match(self, current_context: List[str], new_turn: Dict) -> Tuple[bool, str]:
        """基于规则的 turn 匹配"""
        if not current_context:
            return True, "首个轮次"

        new_msg = new_turn.get('user_message', '')
        last_context = current_context[-1] if current_context else ""

        if last_context and new_msg:
            last_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', last_context.lower()))
            new_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', new_msg.lower()))
            overlap = len(last_words & new_words)
            if overlap >= 3:
                return True, f"语义重叠({overlap})"
            if overlap >= 1:
                return True, f"部分重叠({overlap})"

        return False, "语义不相关"

    def _rule_based_session_match(self, current_context: List[Dict], new_interaction: Dict) -> Tuple[bool, str]:
        """基于规则的 session 匹配"""
        if not current_context:
            return True, "首个会话"

        last_int = current_context[-1]
        last_topic = last_int.get('topic', '')
        new_topic = new_interaction.get('topic', '')

        if last_topic and new_topic:
            last_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', last_topic.lower()))
            new_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', new_topic.lower()))
            overlap = len(last_words & new_words)
            if overlap >= 4:
                return True, f"主题相关({overlap})"
            if overlap >= 2:
                return True, f"部分相关({overlap})"

        return False, "主题不相关"


class TurnIdentifier:
    """识别 turns（单次问答对）"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()

    def identify_all_turns(self):
        """识别所有 turns"""
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
                current_turn = {
                    'user_id': msg_id,
                    'user_content': content,
                    'user_timestamp': timestamp,
                    'assistant_id': None,
                    'assistant_content': None,
                    'assistant_timestamp': None
                }
                user_in_turn = True

            elif role == 'assistant' and user_in_turn and current_turn:
                current_turn['assistant_id'] = msg_id
                current_turn['assistant_content'] = content
                current_turn['assistant_timestamp'] = timestamp

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
            INSERT INTO turns (id, start_time, end_time, user_message, assistant_response, message_count)
            VALUES (?, ?, ?, ?, ?, 2)
        """, (
            turn_id,
            turn_data['user_timestamp'],
            turn_data['assistant_timestamp'],
            turn_data['user_content'],
            turn_data['assistant_content']
        ))

        self.cursor.execute("""
            UPDATE sessions SET turn_id = ? WHERE id IN (?, ?)
        """, (turn_id, turn_data['user_id'], turn_data['assistant_id']))


class LLMDrivenInteractionIdentifier:
    """LLM 驱动的 interaction 识别"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()
        self.matcher = LLMDrivenSemanticMatcher()

    def identify_all_interactions(self):
        """识别所有 interactions"""
        print("\n🔍 步骤 2: 识别 interactions (LLM 驱动)...")

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
        context_messages = []

        for turn_id, user_msg, start_time in turns:
            if not current_interaction:
                current_interaction = [turn_id]
                context_messages = [user_msg or ""]
            else:
                should_add, reason = self.matcher.match_turn_to_interaction(
                    context_messages, {'user_message': user_msg}
                )

                if should_add:
                    current_interaction.append(turn_id)
                    context_messages.append(user_msg or "")
                else:
                    self._create_interaction(current_interaction_id, current_interaction, context_messages)
                    interactions_created += 1

                    current_interaction_id = str(uuid.uuid4())
                    current_interaction = [turn_id]
                    context_messages = [user_msg or ""]

        if current_interaction:
            self._create_interaction(current_interaction_id, current_interaction, context_messages)
            interactions_created += 1

        self.conn.commit()
        print(f"  ✅ 已创建 {interactions_created} 个 interactions")
        return interactions_created

    def _create_interaction(self, interaction_id: str, turn_ids: List[str], contexts: List[str]):
        """创建 interaction 记录"""
        if not turn_ids:
            return

        placeholders = ','.join('?' * len(turn_ids))

        self.cursor.execute(f"""
            SELECT MIN(start_time), MAX(start_time), COUNT(*)
            FROM turns WHERE id IN ({placeholders})
        """, turn_ids)

        min_time, max_time, count = self.cursor.fetchone()

        if isinstance(min_time, str):
            min_time_ts = datetime.fromisoformat(min_time.replace(' ', 'T')).timestamp()
        else:
            min_time_ts = min_time or 0

        if isinstance(max_time, str):
            max_time_ts = datetime.fromisoformat(max_time.replace(' ', 'T')).timestamp()
        else:
            max_time_ts = max_time or 0

        duration = (max_time_ts - min_time_ts) / 60 if min_time and max_time else 0

        topic = contexts[0][:80] if contexts and contexts[0] else "未知主题"

        self.cursor.execute("""
            INSERT INTO interactions (id, start_time, end_time, duration_minutes, turn_count, topic_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (interaction_id, min_time, max_time, duration, count, topic))

        self.cursor.execute(f"""
            UPDATE turns SET interaction_id = ? WHERE id IN ({placeholders})
        """, [interaction_id] + turn_ids)

        self.cursor.execute(f"""
            UPDATE sessions SET interaction_id = ?
            WHERE turn_id IN ({placeholders})
        """, [interaction_id] + turn_ids)


class LLMDrivenSemanticSessionIdentifier:
    """LLM 驱动的 semantic_session 识别"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()
        self.matcher = LLMDrivenSemanticMatcher()

    def identify_all_semantic_sessions(self):
        """识别所有 semantic_sessions"""
        print("\n🔍 步骤 3: 识别 semantic_sessions (LLM 驱动)...")

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
        context_interactions = []

        for int_id, topic, start_time in interactions:
            new_interaction = {'topic': topic, 'start_time': start_time}

            if not current_session_interactions:
                current_session_interactions = [int_id]
                context_interactions = [new_interaction]
            else:
                should_add, reason = self.matcher.match_interaction_to_session(
                    context_interactions, new_interaction
                )

                if should_add:
                    current_session_interactions.append(int_id)
                    context_interactions.append(new_interaction)
                else:
                    self._create_semantic_session(current_session_id, current_session_interactions)
                    sessions_created += 1

                    current_session_id = str(uuid.uuid4())
                    current_session_interactions = [int_id]
                    context_interactions = [new_interaction]

        if current_session_interactions:
            self._create_semantic_session(current_session_id, current_session_interactions)
            sessions_created += 1

        self.conn.commit()
        print(f"  ✅ 已创建 {sessions_created} 个 semantic_sessions")
        return sessions_created

    def _create_semantic_session(self, session_id: str, int_ids: List[str]):
        """创建 semantic_session 记录"""
        if not int_ids:
            return

        placeholders = ','.join('?' * len(int_ids))

        self.cursor.execute(f"""
            SELECT MIN(start_time), MAX(end_time), SUM(turn_count), COUNT(*)
            FROM interactions WHERE id IN ({placeholders})
        """, int_ids)

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

        self.cursor.execute(f"""
            SELECT topic_summary FROM interactions WHERE id = ?
        """, (int_ids[0],))
        title_row = self.cursor.fetchone()
        title = title_row[0][:80] if title_row and title_row[0] else "未命名会话"

        self.cursor.execute("""
            INSERT INTO semantic_sessions
            (id, title, start_time, end_time, duration_minutes, interaction_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, title, min_time, max_time, duration, int_count, 'active'))

        for int_id in int_ids:
            self.cursor.execute(f"""
                SELECT id FROM turns WHERE interaction_id = ?
            """, (int_id,))
            turn_ids = [r[0] for r in self.cursor.fetchall() if r[0]]

            if turn_ids:
                turn_placeholders = ','.join('?' * len(turn_ids))
                self.cursor.execute(f"""
                    UPDATE sessions SET semantic_session_id = ?
                    WHERE turn_id IN ({turn_placeholders})
                """, [session_id] + turn_ids)


def run_llm_hierarchy_identification():
    """执行完整的三层级识别（LLM 驱动）"""
    print("\n" + "="*70)
    print("Flow Ecosystem V7.3 LLM 驱动的层级识别引擎")
    print("="*70)

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")

    try:
        print("\n🤖 LLM 语义匹配引擎初始化...")
        matcher = LLMDrivenSemanticMatcher()

        turn_identifier = TurnIdentifier(conn)
        turns_count = turn_identifier.identify_all_turns()

        interaction_identifier = LLMDrivenInteractionIdentifier(conn)
        interactions_count = interaction_identifier.identify_all_interactions()

        session_identifier = LLMDrivenSemanticSessionIdentifier(conn)
        sessions_count = session_identifier.identify_all_semantic_sessions()

        print("\n" + "="*70)
        print("识别完成汇总 (LLM 驱动)")
        print("="*70)
        print(f"  📊 turns: {turns_count}")
        print(f"  📊 interactions: {interactions_count}")
        print(f"  📊 semantic_sessions: {sessions_count}")

    except Exception as e:
        print(f"\n❌ 识别失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    run_llm_hierarchy_identification()
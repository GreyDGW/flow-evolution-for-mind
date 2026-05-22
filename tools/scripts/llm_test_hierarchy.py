#!/usr/bin/env python3
"""
Flow Ecosystem V7.3 LLM 驱动的层级识别引擎（测试版）
只处理前300条消息，用于验证 LLM 是否能正常工作
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
MAX_MESSAGES = 300

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

        prompt = f"""判断以下新的对话轮次（turn）是否与之前的对话属于同一语义会话（interaction）。

【之前的对话上下文】
{context_text}

【新的对话轮次】
用户消息: {new_turn.get('user_message', '')[:150]}

请用 JSON 格式回答：
{{"should_add": true/false, "reason": "原因", "confidence": 0.0-1.0}}
"""

        try:
            response = self.llm.generate(prompt, max_tokens=150)
            result = json.loads(response)
            should_add = result.get('should_add', False)
            reason = result.get('reason', 'LLM判断')
            return should_add, reason
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}")
            return self._rule_based_turn_match(current_context, new_turn)

    def _rule_based_turn_match(self, current_context: List[str], new_turn: Dict) -> Tuple[bool, str]:
        """基于规则的匹配"""
        if not current_context:
            return True, "首个轮次"

        new_msg = new_turn.get('user_message', '')
        last_context = current_context[-1] if current_context else ""

        if last_context and new_msg:
            last_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', last_context.lower()))
            new_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', new_msg.lower()))
            overlap = len(last_words & new_words)
            if overlap >= 2:
                return True, f"语义重叠({overlap})"

        return False, "语义不相关"


def run_test():
    """运行测试版本"""
    print("\n" + "="*70)
    print("Flow Ecosystem V7.3 LLM 驱动层级识别（测试版 - 前300条）")
    print("="*70)

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")

    try:
        print("\n🤖 LLM 语义匹配引擎初始化...")
        matcher = LLMDrivenSemanticMatcher()
        print(f"    LLM 状态: {'已启用' if matcher.use_llm else '未启用'}")

        print(f"\n🔍 获取前 {MAX_MESSAGES} 条消息...")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, role, content_text, timestamp
            FROM sessions
            WHERE is_valid_for_analysis = 1
            AND role IN ('user', 'assistant')
            ORDER BY timestamp
            LIMIT ?
        """, (MAX_MESSAGES,))

        messages = cursor.fetchall()
        print(f"  ✅ 获取到 {len(messages)} 条消息")

        turns_created = 0
        current_turn = None
        user_in_turn = False
        interaction_count = 0
        current_interaction = []
        context_messages = []

        for msg_id, role, content, timestamp in messages:
            if role == 'user':
                if user_in_turn and current_turn:
                    pass

                current_turn = {
                    'user_id': msg_id,
                    'user_content': content,
                    'timestamp': timestamp
                }
                user_in_turn = True

            elif role == 'assistant' and user_in_turn and current_turn:
                current_turn['assistant_id'] = msg_id
                current_turn['assistant_content'] = content

                turn_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR IGNORE INTO turns (id, start_time, user_message, assistant_response, message_count)
                    VALUES (?, ?, ?, ?, 2)
                """, (turn_id, current_turn['timestamp'], current_turn['user_content'], current_turn['assistant_content']))

                turns_created += 1

                if not current_interaction:
                    current_interaction = [turn_id]
                    context_messages = [current_turn['user_content'] or ""]
                else:
                    should_add, reason = matcher.match_turn_to_interaction(
                        context_messages, {'user_message': current_turn['user_content']}
                    )

                    print(f"    Turn {turns_created}: {'✅ 加入' if should_add else '❌ 新会话'} - {reason}")

                    if should_add:
                        current_interaction.append(turn_id)
                        context_messages.append(current_turn['user_content'] or "")
                    else:
                        if current_interaction:
                            interaction_id = str(uuid.uuid4())
                            cursor.execute("""
                                INSERT INTO interactions (id, start_time, turn_count, topic_summary)
                                VALUES (?, ?, ?, ?)
                            """, (interaction_id, current_interaction[0], len(current_interaction), context_messages[0][:80] if context_messages else ""))

                            cursor.execute("""
                                UPDATE turns SET interaction_id = ? WHERE id = ?
                            """, (interaction_id, current_interaction[0]))

                            for tid in current_interaction[1:]:
                                cursor.execute("""
                                    UPDATE turns SET interaction_id = ? WHERE id = ?
                                """, (interaction_id, tid))

                            interaction_count += 1

                        current_interaction = [turn_id]
                        context_messages = [current_turn['user_content'] or ""]

                current_turn = None
                user_in_turn = False

        if current_interaction:
            interaction_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO interactions (id, start_time, turn_count, topic_summary)
                VALUES (?, ?, ?, ?)
            """, (interaction_id, current_interaction[0], len(current_interaction), context_messages[0][:80] if context_messages else ""))

            for tid in current_interaction:
                cursor.execute("""
                    UPDATE turns SET interaction_id = ? WHERE id = ?
                """, (interaction_id, tid))

            interaction_count += 1

        conn.commit()

        print("\n" + "="*70)
        print("测试结果汇总")
        print("="*70)
        print(f"  📊 处理消息数: {len(messages)}")
        print(f"  📊 创建 turns: {turns_created}")
        print(f"  📊 创建 interactions: {interaction_count}")

        cursor.execute("""
            SELECT COUNT(*) FROM turns WHERE interaction_id IS NOT NULL
        """)
        turns_with_interaction = cursor.fetchone()[0]
        print(f"  📊 turns 已关联: {turns_with_interaction}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    run_test()
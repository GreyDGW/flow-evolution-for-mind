from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import sqlite3
import json
import re

TIMEOUT_MINUTES = 15

try:
    from openclaw_flow_plugin.core.llm_manager import LLMManager
    LLM_AVAILABLE = True
except ImportError:
    try:
        from llm_manager import LLMManager
        LLM_AVAILABLE = True
    except ImportError:
        LLM_AVAILABLE = False
        print("⚠️ LLMManager未找到，将使用规则过滤")


def parse_timestamp(ts):
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace(' ', 'T'))
            return dt.timestamp()
        except:
            try:
                dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f')
                return dt.timestamp()
            except:
                return datetime.now().timestamp()
    return datetime.now().timestamp()


def is_valid_user_message(content: str) -> bool:
    if content is None or len(content) < 3:
        return False

    invalid_patterns = [
        r'^\{.*\}$',
        r'^```',
        r'^\[.*\]$',
        r'^#{1,6}\s',
        r'^\|\s',
        r'^•\s',
        r'^-{3,}$',
        r'^={3,}$',
        r'^[0-9\s\[\]]+$',
        r'^[0-9]+$',
        r'^GMT.*\d+$',
        r'^A new session was started',
        r'^bootstrap is still pending',
        r'^\[cron:',
        r'^You are FlowGuard',
        r'^检查 memory/flowguard',
        r'^只报告问题',
        r'^\d+\s+GMT.*\]$',
        r'^\d+\s+GMT.*\]\s*\d+$',
        r'^[0-9\]\s]+$',
    ]

    for pattern in invalid_patterns:
        if re.match(pattern, content.strip()):
            return False

    return True


def extract_clean_goal(content: str) -> Optional[str]:
    if not is_valid_user_message(content):
        return None

    content = content.strip()
    content = re.sub(r'^[^，。！？：:]+[：:]\s*', '', content)
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content = re.sub(r'\[.*?\]', '', content)
    content = re.sub(r'【.*?】', '', content)

    if len(content) < 5 or len(content) > 200:
        return None

    return content


class ConversationTurn:
    def __init__(self, turn_id: int):
        self.turn_id = turn_id
        self.user_message = None
        self.assistant_messages = []
        self.timestamp = None
        self.agent_id = None
        self.extracted_goals = []

    def is_complete(self):
        return self.user_message is not None and len(self.assistant_messages) > 0

    def get_turn_context(self):
        context = []
        if self.user_message:
            context.append(f"用户: {self.user_message[:200]}")
        for i, msg in enumerate(self.assistant_messages):
            context.append(f"助手{i+1}: {msg[:200]}")
        return "\n".join(context)


class ConversationSession:
    def __init__(self, session_id: int, start_time: float):
        self.session_id = session_id
        self.start_time = start_time
        self.last_message_time = start_time
        self.messages = []
        self.turns = []
        self.current_turn = None
        self.user_messages = []
        self.assistant_messages = []
        self.clean_user_messages = []
        self.agents_involved = set()
        self.goals = []
        self.pdca_stages = []
        self.flow_states = []
        self.evolution_signals = []
        self.llm_validated_goals = []

    def add_message(self, role: str, content: str, timestamp: float, agent_id: str = None):
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': timestamp,
            'agent_id': agent_id
        })
        self.last_message_time = timestamp

        if agent_id:
            self.agents_involved.add(agent_id)

        if role == 'user':
            self.user_messages.append(content)
            clean = extract_clean_goal(content)
            if clean:
                self.clean_user_messages.append(clean)
            
            self.current_turn = ConversationTurn(len(self.turns) + 1)
            self.current_turn.user_message = content
            self.current_turn.timestamp = timestamp
            self.current_turn.agent_id = agent_id
        elif role == 'assistant':
            self.assistant_messages.append(content)
            if self.current_turn:
                self.current_turn.assistant_messages.append(content)

    def finalize_turn(self):
        if self.current_turn and self.current_turn.is_complete():
            self.turns.append(self.current_turn)
            self.current_turn = None

    def is_timeout(self, current_time: float) -> bool:
        return (current_time - self.last_message_time) > (TIMEOUT_MINUTES * 60)

    def complete_sessions(self):
        if self.current_turn and self.current_turn.user_message:
            self.turns.append(self.current_turn)

    def get_full_context(self) -> str:
        context_parts = []
        for msg in self.messages:
            role = msg['role']
            content = msg['content'] or ''
            agent = msg.get('agent_id', '')
            if agent:
                context_parts.append(f"{role}@{agent}: {content[:200]}")
            else:
                context_parts.append(f"{role}: {content[:200]}")
        return "\n".join(context_parts)

    def get_user_context(self) -> str:
        return "\n".join([f"用户: {msg[:200]}" for msg in self.user_messages])

    def get_clean_user_context(self) -> str:
        return "\n".join([msg[:200] for msg in self.clean_user_messages])

    def get_turns_context(self) -> List[str]:
        contexts = []
        for turn in self.turns:
            contexts.append(turn.get_turn_context())
        return contexts

    def __len__(self):
        return len(self.messages)

    def get_full_context(self) -> str:
        context_parts = []
        for msg in self.messages:
            role = msg['role']
            content = msg['content'] or ''
            agent = msg.get('agent_id', '')
            if agent:
                context_parts.append(f"{role}@{agent}: {content[:200]}")
            else:
                context_parts.append(f"{role}: {content[:200]}")
        return "\n".join(context_parts)

    def get_user_context(self) -> str:
        return "\n".join([f"用户: {msg[:200]}" for msg in self.user_messages])

    def get_clean_user_context(self) -> str:
        return "\n".join([msg[:200] for msg in self.clean_user_messages])

    def __len__(self):
        return len(self.messages)


class SessionManager:
    def __init__(self, db_path: str = 'flow_ecosystem.db', use_llm_validation: bool = False):
        self.db_path = db_path
        self.current_session = None
        self.sessions = []
        self.TIMEOUT = TIMEOUT_MINUTES * 60
        self.use_llm_validation = use_llm_validation and LLM_AVAILABLE
        if self.use_llm_validation:
            self.llm = LLMManager()
            print("✅ 启用LLM语义验证")
        else:
            print("⚠️ 使用规则过滤进行目标验证")

    def load_sessions(self, days: int = 7) -> List[ConversationSession]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        cursor.execute("""
            SELECT id, role, content_text, timestamp, agent_id
            FROM sessions
            WHERE timestamp IS NOT NULL AND role IN ('user', 'assistant')
            ORDER BY timestamp
        """, ())

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        current_session = None
        session_id = 0

        for row in rows:
            msg_id, role, content, timestamp, agent_id = row

            if content is None or content == '':
                continue

            ts = parse_timestamp(timestamp)

            if ts < cutoff_time:
                continue

            if current_session is None:
                session_id += 1
                current_session = ConversationSession(session_id, ts)
            elif current_session.is_timeout(ts):
                current_session.complete_sessions()
                if len(current_session) > 0:
                    sessions.append(current_session)
                session_id += 1
                current_session = ConversationSession(session_id, ts)

            current_session.add_message(role, content, ts, agent_id)

        if current_session and len(current_session) > 0:
            current_session.complete_sessions()
            sessions.append(current_session)

        self.sessions = sessions
        return sessions

    def analyze_session(self, session: ConversationSession) -> Dict:
        analysis = {
            'session_id': session.session_id,
            'message_count': len(session.messages),
            'user_message_count': len(session.user_messages),
            'clean_user_message_count': len(session.clean_user_messages),
            'assistant_message_count': len(session.assistant_messages),
            'agents_involved': list(session.agents_involved),
            'agent_count': len(session.agents_involved),
            'duration_minutes': (session.last_message_time - session.start_time) / 60,
            'goals': [],
            'pdca_stages': [],
            'flow_indicators': [],
            'evolution_indicators': [],
            'overall_goal': None,
            'closure_score': 0.0,
            'flow_depth': 0.0,
            'evolution_score': 0.0,
            'confidence': 0.0,
            'source': 'local'
        }

        self._detect_pdca_stages(session, analysis)
        self._detect_flow_indicators(session, analysis)
        self._detect_evolution_indicators(session, analysis)
        self._extract_goals_from_session(session, analysis)
        self._calculate_metrics(analysis)

        return analysis

    def _detect_pdca_stages(self, session: ConversationSession, analysis: Dict):
        pdca_patterns = {
            'plan': [
                '计划', '打算', '准备', '想要', '要实现', '目标',
                '想做', '要做', '应该', '可能', '也许', '要不要'
            ],
            'do': [
                '做', '执行', '进行', '开始', '试试', '试试看',
                '搞', '弄', '试', '写', '开发', '创建', '修改'
            ],
            'check': [
                '检查', '验证', '看看', '结果', '完成了', '看看结果',
                '好了', '成功', '完成', '结束', '跑', '运行'
            ],
            'adjust': [
                '调整', '修改', '优化', '改进', '重新', '换一种',
                '不对', '错了', '不行', '不好', '不对', '再'
            ]
        }

        user_context = session.get_clean_user_context()

        for stage, patterns in pdca_patterns.items():
            for pattern in patterns:
                if pattern in user_context:
                    if stage not in analysis['pdca_stages']:
                        analysis['pdca_stages'].append(stage)
                    break

    def _detect_flow_indicators(self, session: ConversationSession, analysis: Dict):
        flow_positive = [
            '专注', '沉浸', '心流', '进入状态', '高效', '有思路', '越做越顺',
            '顺利', '搞定', '完成', '好了', '对了', '可以', '不错'
        ]
        flow_negative = [
            '打断', '中断', '分心', '走神', '卡住', '困惑', '思维混乱',
            '不懂', '不会', '不知道', '忘了', '忘记了', '错了', '不对'
        ]
        flow_neutral = [
            '继续', '接着', '下一个', '下一步', '然后', '再', '还'
        ]

        user_context = session.get_clean_user_context()

        for indicator in flow_positive:
            if indicator in user_context:
                analysis['flow_indicators'].append({'type': 'positive', 'indicator': indicator})

        for indicator in flow_negative:
            if indicator in user_context:
                analysis['flow_indicators'].append({'type': 'negative', 'indicator': indicator})

        for indicator in flow_neutral:
            if indicator in user_context:
                analysis['flow_indicators'].append({'type': 'neutral', 'indicator': indicator})

    def _detect_evolution_indicators(self, session: ConversationSession, analysis: Dict):
        evolution_positive = [
            '学会了', '掌握了', '理解了', '进步了', '明白了', '找到了', '解决了',
            '知道了', '搞懂了', '清楚了', '认识了', '了解了'
        ]
        evolution_negative = [
            '忘记了', '不懂', '困惑', '还是不会', '没理解', '搞不定',
            '不知道', '不清楚', '不明白', '没搞懂'
        ]

        full_context = session.get_full_context()

        for indicator in evolution_positive:
            if indicator in full_context:
                analysis['evolution_indicators'].append({'type': 'positive', 'indicator': indicator})

        for indicator in evolution_negative:
            if indicator in full_context:
                analysis['evolution_indicators'].append({'type': 'negative', 'indicator': indicator})

    def _is_relevant_to_context(self, goal_text: str, context: str) -> bool:
        goal_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', goal_text))
        context_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', context))
        
        if not goal_words:
            return True
        
        overlap = goal_words & context_words
        return len(overlap) >= max(1, len(goal_words) // 3)

    def _extract_goals_from_turn(self, turn: ConversationTurn) -> List[str]:
        if not turn.user_message:
            return []

        goal_patterns = [
            (r'(帮我|我想|我要|我需要|帮我想|帮我要|帮我做|想让你|帮我查|帮我找|帮我看看|帮我问)([^。！？；]{3,})', 'request'),
            (r'(完成|实现|达成|解决|学习|掌握|精通|学会|做到|达成|到达)([^。！？；]{3,})', 'goal'),
            (r'(修改|调整|优化|改进|更新|改变|修正|重构)([^。！？；]{3,})', 'modification'),
            (r'(创建|建立|开发|设计|构建|搭建|新建|新增)([^。！？；]{3,})', 'creation'),
            (r'(分析|研究|调研|了解|理解|搞懂|搞清楚|弄清楚)([^。！？；]{3,})', 'analysis'),
            (r'(测试|验证|检查|调试|排查|试试)([^。！？；]{3,})', 'testing'),
            (r'(告诉我|跟我说|给我讲|给我介绍|给我说明)([^。！？；]{3,})', 'inquiry'),
            (r'(问一下|想问|想请教|想问问)([^。！？；]{3,})', 'inquiry'),
            (r'(为什么|怎么回事|什么原因|怎么回|怎么会)([^。！？；]{3,})', 'question'),
        ]

        goals = set()
        clean_msg = extract_clean_goal(turn.user_message)
        
        if not clean_msg:
            return []

        for pattern, goal_type in goal_patterns:
            matches = re.finditer(pattern, clean_msg)
            for match in matches:
                goal_text = (match.group(1) + match.group(2)).strip()
                goal_text = re.sub(r'[。！？；,，"\']+$', '', goal_text)

                if 3 <= len(goal_text) <= 100:
                    goals.add(goal_text)

        return list(goals)

    def _validate_goal_with_llm(self, goal_text: str, context: str = "") -> bool:
        if not self.use_llm_validation:
            return self._rule_based_validation(goal_text)
        
        return self.llm.is_valid_goal(goal_text)

    def _rule_based_validation(self, goal_text: str) -> bool:
        if not goal_text or len(goal_text) < 5:
            return False
        
        invalid_patterns = [
            r'^[一二三四五六七八九十0-9]+$',
            r'^[，。！？、；：]+$',
            r'^\s*$',
            r'^[a-zA-Z]\s*$',
            r'^是|不是|对|不对|好|不好$',
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, goal_text.strip()):
                return False
        
        valid_patterns = [
            '帮我', '我想', '我要', '我需要', '完成', '实现', '达成', '解决',
            '学习', '掌握', '开发', '创建', '修改', '调整', '优化', '分析',
            '研究', '了解', '理解', '设计', '实现', '测试', '验证', '检查'
        ]
        
        if any(pattern in goal_text for pattern in valid_patterns):
            return True
        
        return len(goal_text) > 10

    def _extract_goals_from_session(self, session: ConversationSession, analysis: Dict):
        session_context = session.get_full_context()
        
        session_goals = set()
        
        if not session.clean_user_messages:
            analysis['goals'] = []
            analysis['overall_goal'] = None
            analysis['turn_goals_count'] = 0
            analysis['turn_count'] = len(session.turns)
            return
        
        goal_patterns = [
            (r'(帮我|我想|我要|我需要|帮我想|帮我要|帮我做|想让你|帮我查|帮我找|帮我看看|帮我问|给我)([^。！？；]{4,})', 'request'),
            (r'(完成|实现|达成|解决|学习|掌握|精通|学会|做到|达成|到达)([^。！？；]{4,})', 'goal'),
            (r'(修改|调整|优化|改进|更新|改变|修正|重构)([^。！？；]{4,})', 'modification'),
            (r'(创建|建立|开发|设计|构建|搭建|新建|新增)([^。！？；]{4,})', 'creation'),
            (r'(分析|研究|调研|了解|理解|搞懂|搞清楚|弄清楚)([^。！？；]{4,})', 'analysis'),
            (r'(测试|验证|检查|调试|排查|试试)([^。！？；]{4,})', 'testing'),
            (r'(告诉我|跟我说|给我讲|给我介绍|给我说明|跟我说说)([^。！？；]{4,})', 'inquiry'),
            (r'(问一下|想问|想请教|想问问|我想问|我想知道|想了解)([^。！？；]{4,})', 'inquiry'),
            (r'(为什么|怎么回事|什么原因|怎么回|怎么会|是什么|有什么)([^。！？；]{4,})', 'question'),
            (r'(什么是|什么叫|如何|怎么|怎样)([^。！？；]{3,})', 'question'),
            (r'(是什么意思)([^。！？；]+)', 'question'),
            (r'(用|使用|基于)([^。！？；]{4,})', 'usage'),
            (r'(切换到)([^。！？；]{2,})', 'switch'),
            (r'(推荐)([^。！？；]{2,})', 'recommendation'),
            (r'(的替代品)([^。！？；]{2,})', 'alternative'),
        ]

        for clean_msg in session.clean_user_messages:
            for pattern, goal_type in goal_patterns:
                matches = re.finditer(pattern, clean_msg)
                for match in matches:
                    goal_text = (match.group(1) + match.group(2)).strip()
                    goal_text = re.sub(r'[。！？；,，"\']+$', '', goal_text)

                    if 5 <= len(goal_text) <= 100:
                        if self._validate_goal_with_llm(goal_text, session_context):
                            session_goals.add(goal_text)

        if len(session_goals) > 0:
            first_turn_user_msg = session.clean_user_messages[0] if session.clean_user_messages else ""
            
            primary_goal = None
            for goal in session_goals:
                if goal[:30] in first_turn_user_msg[:50]:
                    primary_goal = goal
                    break
            
            if primary_goal is None:
                primary_goal = list(session_goals)[0]
            
            analysis['overall_goal'] = primary_goal

        analysis['goals'] = list(session_goals)[:5]
        analysis['turn_goals_count'] = len(session_goals)
        analysis['turn_count'] = len(session.turns)

    def _calculate_metrics(self, analysis: Dict):
        pdca_count = len(analysis['pdca_stages'])
        if pdca_count == 4:
            analysis['closure_score'] = 100.0
        elif pdca_count == 3:
            analysis['closure_score'] = 75.0
        elif pdca_count == 2:
            analysis['closure_score'] = 50.0
        elif pdca_count == 1:
            analysis['closure_score'] = 25.0
        else:
            analysis['closure_score'] = 0.0

        positive_count = sum(1 for i in analysis['flow_indicators'] if i['type'] == 'positive')
        negative_count = sum(1 for i in analysis['flow_indicators'] if i['type'] == 'negative')
        total_count = len(analysis['flow_indicators'])

        if total_count == 0:
            analysis['flow_depth'] = 0.5
        else:
            analysis['flow_depth'] = (positive_count - negative_count) / total_count

        evo_positive = sum(1 for i in analysis['evolution_indicators'] if i['type'] == 'positive')
        evo_negative = sum(1 for i in analysis['evolution_indicators'] if i['type'] == 'negative')
        evo_total = evo_positive + evo_negative

        if evo_total == 0:
            analysis['evolution_score'] = 0.0
        else:
            analysis['evolution_score'] = (evo_positive - evo_negative) / evo_total

        msg_count = analysis['message_count']
        clean_msg_count = analysis['clean_user_message_count']
        pdca_count = len(analysis['pdca_stages'])
        confidence = min(0.9, 0.4 + clean_msg_count * 0.1 + pdca_count * 0.1)
        analysis['confidence'] = confidence

    def analyze_all_sessions(self, days: int = 7) -> List[Dict]:
        sessions = self.load_sessions(days)
        results = []

        for session in sessions:
            if len(session) > 0:
                analysis = self.analyze_session(session)
                results.append(analysis)

        return results

    def save_analyses(self, analyses: List[Dict]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM session_analyses")

        for analysis in analyses:
            cursor.execute("""
                INSERT INTO session_analyses
                (session_id, message_count, user_message_count, clean_user_message_count, 
                 assistant_message_count, agents_involved, agent_count, duration_minutes,
                 goals_json, pdca_stages, flow_depth, evolution_score, closure_score,
                 confidence, overall_goal, source, turn_count, turn_goals_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis['session_id'],
                analysis['message_count'],
                analysis['user_message_count'],
                analysis['clean_user_message_count'],
                analysis['assistant_message_count'],
                ','.join(analysis['agents_involved']),
                analysis['agent_count'],
                analysis['duration_minutes'],
                json.dumps(analysis['goals'], ensure_ascii=False),
                ','.join(analysis['pdca_stages']),
                analysis['flow_depth'],
                analysis['evolution_score'],
                analysis['closure_score'],
                analysis['confidence'],
                analysis['overall_goal'],
                analysis['source'],
                analysis.get('turn_count', 0),
                analysis.get('turn_goals_count', 0)
            ))

        conn.commit()
        conn.close()


def create_session_analyses_table(db_path: str = 'flow_ecosystem.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            message_count INTEGER,
            user_message_count INTEGER,
            clean_user_message_count INTEGER,
            assistant_message_count INTEGER,
            agents_involved TEXT,
            agent_count INTEGER,
            duration_minutes REAL,
            goals_json TEXT,
            pdca_stages TEXT,
            flow_depth REAL,
            evolution_score REAL,
            closure_score REAL,
            confidence REAL,
            overall_goal TEXT,
            source TEXT,
            turn_count INTEGER,
            turn_goals_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ session_analyses表创建成功")


if __name__ == '__main__':
    create_session_analyses_table()

    manager = SessionManager(use_llm_validation=True)
    analyses = manager.analyze_all_sessions(days=7)

    print("\n" + "=" * 70)
    print("📊 跨Agent会话分析报告（一轮对话级别）")
    print("=" * 70)
    print(f"总会话数: {len(analyses)}")

    if analyses:
        avg_closure = sum(a['closure_score'] for a in analyses) / len(analyses)
        avg_flow = sum(a['flow_depth'] for a in analyses) / len(analyses)
        avg_evolution = sum(a['evolution_score'] for a in analyses) / len(analyses)
        avg_agents = sum(a['agent_count'] for a in analyses) / len(analyses)
        avg_turns = sum(a.get('turn_count', 0) for a in analyses) / len(analyses)
        avg_turn_goals = sum(a.get('turn_goals_count', 0) for a in analyses) / len(analyses)

        identified_goals = sum(1 for a in analyses if a['overall_goal'] is not None)
        multi_agent_sessions = sum(1 for a in analyses if a['agent_count'] > 1)

        print(f"平均闭环分数: {avg_closure:.1f}")
        print(f"平均心流深度: {avg_flow:.2f}")
        print(f"平均认知进化: {avg_evolution:.2f}")
        print(f"目标识别率: {identified_goals}/{len(analyses)} ({identified_goals/len(analyses)*100:.1f}%)")
        print(f"平均涉及Agent数: {avg_agents:.1f}")
        print(f"跨Agent会话数: {multi_agent_sessions}")
        print(f"平均对话轮数: {avg_turns:.1f}")
        print(f"平均每轮目标数: {avg_turn_goals:.1f}")

        print("\n📋 前10个会话详情:")
        for i, a in enumerate(analyses[:10]):
            print(f"\n会话{i+1}:")
            print(f"  - 消息数: {a['message_count']} (用户: {a['user_message_count']}, 有效: {a['clean_user_message_count']})")
            print(f"  - 对话轮数: {a.get('turn_count', 0)}")
            print(f"  - 时长: {a['duration_minutes']:.1f}分钟")
            print(f"  - 涉及Agent: {a['agent_count']} 个")
            if a['agents_involved']:
                print(f"    Agent列表: {a['agents_involved']}")
            print(f"  - PDCA阶段: {a['pdca_stages'] or '无'}")
            print(f"  - 闭环分数: {a['closure_score']:.1f}")
            print(f"  - 心流深度: {a['flow_depth']:.2f}")
            print(f"  - 整体目标: {a['overall_goal'] or '未识别'}")
            if a['goals']:
                print(f"  - 提取目标: {a['goals'][:2]}")

        manager.save_analyses(analyses)
        print(f"\n✅ 已保存 {len(analyses)} 条分析结果")
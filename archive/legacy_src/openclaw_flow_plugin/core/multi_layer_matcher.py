import difflib
from typing import List, Dict, Tuple, Optional
import re

GOAL_KEYWORDS = {
    '学习': ['学习', '学', '学习一下', '了解', '掌握', '学会', '钻研', '研究', '自学', '进修', '攻读'],
    '修改': ['修改', '调整', '优化', '改进', '改动', '更新', '变更', '修正', '改版', '翻新'],
    '创建': ['创建', '建立', '开发', '编写', '制作', '生成', '构建', '设计', '搭建', '打造', '创立'],
    '完成': ['完成', '做完', '搞定', '结束', '实现', '达成', '竣工', '了结', '做完了', '完工'],
    '帮助': ['帮我', '帮忙', '协助', '支援', '援助', '支持', '帮一下', '搭把手'],
    '分析': ['分析', '研究', '剖析', '解析', '探讨', '研究分析', '研判', '解析', '评估'],
    '设计': ['设计', '规划', '策划', '构想', '构思', '谋划', '布局'],
    '解决': ['解决', '处理', '搞定', '攻克', '化解', '处置', '应对', '克服'],
    '开发': ['开发', '研发', '制作', '构建', '打造', '研制', '开发设计'],
    '测试': ['测试', '验证', '检验', '调试', '试运行', '试用', '检测'],
    '写': ['写', '编写', '撰写', '书写', '记录', '录入', '输入'],
    '做': ['做', '制作', '弄', '搞', '干', '执行', '操作'],
    '实现': ['实现', '达成', '落实', '兑现', '完成'],
    '构建': ['构建', '搭建', '建立', '架设', '组装'],
    '优化': ['优化', '改进', '升级', '改良', '提升'],
    '整理': ['整理', '梳理', '整顿', '清理', '归纳'],
    '复习': ['复习', '回顾', '温习', '重温', '巩固'],
    '探索': ['探索', '探究', '摸索', '探寻', '发掘'],
    '实践': ['实践', '实操', '演练', '练习', '操作']
}

CONTEXT_KEYWORDS = {
    'flow': ['flow', 'ecosystem', 'flow ecosystem', 'flow生态', '生态系统'],
    'python': ['python', '编程', '代码', '脚本', '开发'],
    '文档': ['文档', '文档编写', '文档整理', '文档更新'],
    '系统': ['系统', '平台', '架构', '框架'],
    '技能': ['技能', '功能', '能力', '特性']
}


class MultiLayerMatcher:
    def __init__(self, fuzzy_threshold: float = 0.65, similarity_threshold: float = 0.25):
        self.fuzzy_threshold = fuzzy_threshold
        self.similarity_threshold = similarity_threshold
        self.context_history = []

    def add_context(self, message: str):
        """添加上下文历史"""
        self.context_history.append(message)
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]

    def _get_enhanced_message(self, message: str) -> str:
        """结合上下文增强消息"""
        if len(self.context_history) > 0 and len(message) <= 10:
            enhanced = message + " " + " ".join(self.context_history[-3:])
            return enhanced
        return message

    def _exact_match(self, message: str, goal_text: str) -> bool:
        message_lower = message.lower()
        goal_lower = goal_text.lower()

        for category, keywords in GOAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower and keyword in goal_lower:
                    return True

        if goal_lower in message_lower or message_lower in goal_lower:
            return True

        return False

    def _fuzzy_match(self, message: str, goal_text: str) -> bool:
        message_words = message.lower().split()
        goal_words = goal_text.lower().split()

        for msg_word in message_words:
            for goal_word in goal_words:
                similarity = difflib.SequenceMatcher(None, msg_word, goal_word).ratio()
                if similarity >= self.fuzzy_threshold:
                    return True

        return False

    def _semantic_similarity(self, message: str, goal_text: str) -> float:
        message_words = set(message.lower().split())
        goal_words = set(goal_text.lower().split())

        if not goal_words:
            return 0.0

        common_words = message_words.intersection(goal_words)
        jaccard_similarity = len(common_words) / len(goal_words)

        lcs_length = difflib.SequenceMatcher(None, message, goal_text).find_longest_match().size
        lcs_ratio = lcs_length / max(len(message), len(goal_text))

        return (jaccard_similarity + lcs_ratio) / 2

    def _has_context_match(self, message: str, goal_text: str) -> bool:
        """检查是否有上下文匹配"""
        message_lower = message.lower()
        goal_lower = goal_text.lower()

        for category, keywords in CONTEXT_KEYWORDS.items():
            message_has = any(kw in message_lower for kw in keywords)
            goal_has = any(kw in goal_lower for kw in keywords)
            if message_has and goal_has:
                return True

        return False

    def match(self, message: str, goals: List[Dict], use_context: bool = True) -> Tuple[bool, Optional[Dict], float]:
        enhanced_message = self._get_enhanced_message(message) if use_context else message
        message_clean = re.sub(r'[。！？，,、；;：:\"\'\(\)\[\]\{\}]', '', enhanced_message)

        if not message_clean.strip():
            return False, None, 0.0

        best_match = None
        best_score = 0.0

        for goal in goals:
            goal_text = goal.get('declared_text', '')
            if not goal_text:
                continue

            if self._exact_match(message_clean, goal_text):
                return True, goal, 1.0

            if self._fuzzy_match(message_clean, goal_text):
                base_score = 0.8
                if self._has_context_match(message_clean, goal_text):
                    base_score = 0.9
                if base_score > best_score:
                    best_score = base_score
                    best_match = goal

            similarity = self._semantic_similarity(message_clean, goal_text)
            if self._has_context_match(message_clean, goal_text):
                similarity = min(1.0, similarity + 0.2)

            if similarity > self.similarity_threshold and similarity > best_score:
                best_score = similarity
                best_match = goal

        if best_match and best_score >= self.similarity_threshold:
            return True, best_match, best_score

        return False, None, 0.0

    def batch_match(self, message: str, goals: List[Dict], top_n: int = 3, use_context: bool = True) -> List[Tuple[Dict, float]]:
        enhanced_message = self._get_enhanced_message(message) if use_context else message
        message_clean = re.sub(r'[。！？，,、；;：:\"\'\(\)\[\]\{\}]', '', enhanced_message)

        matches = []
        for goal in goals:
            goal_text = goal.get('declared_text', '')
            if not goal_text:
                continue

            if self._exact_match(message_clean, goal_text):
                score = 1.0
                if self._has_context_match(message_clean, goal_text):
                    score = 1.0
                matches.append((goal, score))
            elif self._fuzzy_match(message_clean, goal_text):
                score = 0.8
                if self._has_context_match(message_clean, goal_text):
                    score = 0.9
                matches.append((goal, score))
            else:
                similarity = self._semantic_similarity(message_clean, goal_text)
                if self._has_context_match(message_clean, goal_text):
                    similarity = min(1.0, similarity + 0.2)
                if similarity > 0:
                    matches.append((goal, similarity))

        matches.sort(key=lambda x: x[1], reverse=True)

        return matches[:top_n]


if __name__ == '__main__':
    matcher = MultiLayerMatcher()

    active_goals = [
        {'id': 1, 'declared_text': '学习Python编程', 'time_horizon': 'short'},
        {'id': 2, 'declared_text': '修改flow ecosystem技能', 'time_horizon': 'short'},
        {'id': 3, 'declared_text': '创建个人进化系统', 'time_horizon': 'long'},
        {'id': 4, 'declared_text': '完成API文档', 'time_horizon': 'medium'}
    ]

    test_messages = [
        '我想学习Python',
        '帮我修改flow的技能',
        '编一个个人进化系统',
        'API文档写完了吗',
        '这个怎么做',
        '学Pyhton编程',
        '了解一下flow ecosystem',
        '写代码',
        '做系统',
        '开发功能'
    ]

    print("=" * 70)
    print("🧠 多层匹配方案测试")
    print("=" * 70)

    for msg in test_messages:
        is_match, goal, score = matcher.match(msg, active_goals)
        if is_match:
            print(f"✅ [{score:.2f}] '{msg}' -> '{goal['declared_text']}'")
        else:
            print(f"❌ '{msg}' -> 未匹配到目标")

    print("\n" + "=" * 70)
    print("📊 上下文测试")
    print("=" * 70)

    matcher.add_context("我想开发一个flow ecosystem系统")
    matcher.add_context("需要学习Python编程")

    short_messages = ['这个怎么做', '继续', '下一步']
    for msg in short_messages:
        is_match, goal, score = matcher.match(msg, active_goals)
        if is_match:
            print(f"✅ [{score:.2f}] '{msg}' (带上下文) -> '{goal['declared_text']}'")
        else:
            print(f"❌ '{msg}' (带上下文) -> 未匹配到目标")
#!/usr/bin/env python3
"""
GoalLoader - 从 memory.md 读取用户活跃目标
支持结构化区块 ## Flow-Goals 的解析
"""

import re
from pathlib import Path
from typing import List, Dict


class GoalLoader:
    """目标加载器：从 memory.md 读取活跃目标"""

    DEFAULT_PATH = Path.home() / ".openclaw" / "memory.md"

    def __init__(self, memory_path: Path = None):
        self.memory_path = memory_path or self.DEFAULT_PATH
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """如果 memory.md 不存在，创建默认模板"""
        if not self.memory_path.exists():
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            self.memory_path.write_text(self._default_template(), encoding='utf-8')

    def _default_template(self) -> str:
        """默认 memory.md 模板"""
        return """# Flow Memory - 认知进化追踪

## Flow-Goals

- [长期] 成为系统架构师 | 状态: 稳步推进 | 优先级: P0
- [中期] 完成微服务拆分方案 | 状态: 推进中 | 优先级: P1
- [短期] 优化查询性能 | 状态: 待启动 | 优先级: P2

## Flow-Status

今日心流指数: 0.0
今日认知进化: 0.0

## Flow-Patterns

高频时段: 09:00-12:00
易漂移场景: 饭后、会议后

## Flow-Cognition

最近突破:
待深化概念:
"""

    def load_active_goals(self) -> List[Dict]:
        """
        读取活跃目标（状态为 推进中/稳步推进/进行中）
        返回格式: [{"text": "...", "type": "长期", "status": "推进中", "priority": "P0"}]
        """
        if not self.memory_path.exists():
            return []

        content = self.memory_path.read_text(encoding='utf-8')

        goals_section = self._extract_section(content, "Flow-Goals")
        if not goals_section:
            return []

        goals = []
        for line in goals_section.split('\n'):
            line = line.strip()
            if not line or not line.startswith('-'):
                continue

            goal = self._parse_goal_line(line)
            if goal and self._is_active(goal):
                goals.append(goal)

        goals.sort(key=lambda g: g.get('priority', 'P9'))
        return goals

    def _extract_section(self, content: str, section_name: str) -> str:
        """提取 markdown 区块内容"""
        pattern = rf'##\s*{re.escape(section_name)}\s*\n(.*?)(?=##\s|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _parse_goal_line(self, line: str) -> Dict:
        """
        解析单行目标
        格式: - [类型] 目标文本 | 状态: XXX | 优先级: P0
        """
        line = line[2:].strip() if line.startswith('- ') else line.strip()

        type_match = re.search(r'^\[([^\]]+)\]\s*', line)
        goal_type = type_match.group(1) if type_match else "未知"
        if type_match:
            line = line[type_match.end():].strip()

        status_match = re.search(r'\|\s*状态:\s*([^\|]+?)\s*(?:\||$)', line)
        status = status_match.group(1).strip() if status_match else "未知"

        priority_match = re.search(r'\|\s*优先级:\s*([^\|]+?)\s*(?:\||$)', line)
        priority = priority_match.group(1).strip() if priority_match else "P9"

        text = re.sub(r'\s*\|.*$', '', line).strip()

        return {
            "text": text,
            "type": goal_type,
            "status": status,
            "priority": priority
        }

    def _is_active(self, goal: Dict) -> bool:
        """判断目标是否活跃"""
        active_statuses = {
            "推进中", "稳步推进", "进行中", "活跃", "active", "in_progress"
        }
        return goal.get("status", "") in active_statuses

    def get_all_goals(self) -> List[Dict]:
        """读取所有目标（包括非活跃）"""
        if not self.memory_path.exists():
            return []

        content = self.memory_path.read_text(encoding='utf-8')
        goals_section = self._extract_section(content, "Flow-Goals")
        if not goals_section:
            return []

        goals = []
        for line in goals_section.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                goal = self._parse_goal_line(line)
                if goal:
                    goals.append(goal)
        return goals

    def update_goal_status(self, goal_text: str, new_status: str) -> bool:
        """更新目标状态（用于闭环后标记完成）"""
        if not self.memory_path.exists():
            return False

        content = self.memory_path.read_text(encoding='utf-8')

        old_pattern = rf'(- \[.*?\] .*?{re.escape(goal_text)}.*?)\|\s*状态:\s*[^\|]+'
        new_line = rf'\1| 状态: {new_status}'

        new_content, count = re.subn(old_pattern, new_line, content, count=1)
        if count > 0:
            self.memory_path.write_text(new_content, encoding='utf-8')
            return True
        return False
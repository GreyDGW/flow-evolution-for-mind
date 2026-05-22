"""Active-session filter rules placeholder from chapter 1.3."""

from typing import Iterable


def filter_active_sessions(session_types: Iterable[str]) -> list[str]:
    """
    Keep only user-initiated sessions.

    Exclude:
    - cron
    - heartbeat
    - scheduled jobs
    """
    blocked = {"cron", "heartbeat", "scheduled"}
    return [s for s in session_types if s.lower() not in blocked]


class SessionFilter:
    """会话过滤器"""
    
    def __init__(self):
        self.blocked_types = {"cron", "heartbeat", "scheduled"}
    
    def filter(self, session_types: Iterable[str]) -> list[str]:
        """过滤活跃会话"""
        return filter_active_sessions(session_types)
    
    def is_active(self, session_type: str) -> bool:
        """判断会话是否活跃"""
        return session_type.lower() not in self.blocked_types
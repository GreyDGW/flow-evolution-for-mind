from typing import Dict, Optional


class FlowCommand:
    def __init__(self):
        self.commands = {
            "/flow": self.handle_flow,
            "/flow stats": self.handle_stats,
            "/flow today": self.handle_today,
            "/flow week": self.handle_week,
            "/flow summary": self.handle_summary,
        }
    
    def parse(self, command: str) -> str:
        cmd = command.strip()
        handler = self.commands.get(cmd, self.handle_unknown)
        return handler()
    
    def handle_flow(self) -> str:
        return "Flow 模式已激活"
    
    def handle_stats(self) -> str:
        return "统计功能开发中"
    
    def handle_today(self) -> str:
        return "今日统计开发中"
    
    def handle_week(self) -> str:
        return "周统计开发中"
    
    def handle_summary(self) -> str:
        return "汇总报告开发中"
    
    def handle_unknown(self) -> str:
        return "未知命令"
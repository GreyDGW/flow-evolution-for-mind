import os
from datetime import datetime
from typing import Optional


class MemoryManager:
    def __init__(self, memory_path: str = "MEMORY.md"):
        self.memory_path = memory_path
    
    def load_memory(self) -> str:
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def update_memory(self, content: str) -> bool:
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"更新 MEMORY.md 失败: {e}")
            return False
    
    def append_entry(self, entry: str) -> bool:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(self.memory_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n## 更新 {timestamp}\n{entry}\n")
            return True
        except Exception as e:
            print(f"追加 MEMORY.md 失败: {e}")
            return False
import os
import sqlite3
from datetime import datetime, timedelta

class GoalExtractor:
    """从 Agent MEMORY.md 提取活跃目标，24h 缓存，实体锚点结构"""
    
    def __init__(self, db_path="data/flow_ecosystem.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        self._ensure_table()
        self._llm = None
    
    def _get_llm(self):
        if self._llm is None:
            from plugin.llm_client import DeepSeekLLMClient
            self._llm = DeepSeekLLMClient()
        return self._llm
    
    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_goals (
                agent_id TEXT PRIMARY KEY,
                goals_text TEXT,
                source_mtime REAL,
                extracted_at TEXT,
                expires_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _find_memory_path(self, agent_id):
        """四级路径发现 + 三层降级，保障跨平台兼容性"""
        # 优先级1: 环境变量（用户自定义）
        openclaw_dir = os.environ.get('OPENCLAW_DATA_DIR')
        if openclaw_dir:
            candidates = [
                os.path.join(openclaw_dir, f"agents/{agent_id}/workspace/MEMORY.md"),
                os.path.join(openclaw_dir, "workspace/MEMORY.md"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    return p

        # 优先级2: 配置文件 ~/.flow_evolution/config
        config_path = os.path.expanduser("~/.flow_evolution/config")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('OPENCLAW_DATA_DIR='):
                            openclaw_dir = line.split('=', 1)[1].strip()
                            candidates = [
                                os.path.join(openclaw_dir, f"agents/{agent_id}/workspace/MEMORY.md"),
                                os.path.join(openclaw_dir, "workspace/MEMORY.md"),
                            ]
                            for p in candidates:
                                if os.path.exists(p):
                                    return p
                            break
            except Exception:
                pass

        # 优先级3: 自动探测常见路径（Mac/Linux/Windows）
        common_paths = [
            os.path.expanduser(f"~/.openclaw/agents/{agent_id}/workspace/MEMORY.md"),
            os.path.expanduser("~/.openclaw/workspace/MEMORY.md"),
            os.path.expanduser(f"~/Library/Application Support/openclaw/agents/{agent_id}/workspace/MEMORY.md"),
            os.path.expanduser(f"~/.config/openclaw/agents/{agent_id}/workspace/MEMORY.md"),
            # Windows
            os.path.expanduser(f"~/AppData/Local/openclaw/agents/{agent_id}/workspace/MEMORY.md"),
            os.path.expanduser(f"%LOCALAPPDATA%/openclaw/agents/{agent_id}/workspace/MEMORY.md"),
        ]
        for p in common_paths:
            p = os.path.expandvars(p)  # 展开 %LOCALAPPDATA% 等 Windows 变量
            if os.path.exists(p):
                return p

        # 优先级4: 可配置 fallback（通过 .env 或环境变量指定任意路径）
        custom_memory = os.environ.get('FLOW_MEMORY_MD_PATH')
        if custom_memory and os.path.exists(custom_memory):
            return custom_memory

        return None
    
    def extract(self, agent_id, force_refresh=False):
        if not agent_id:
            return "未声明目标"
        
        memory_path = self._find_memory_path(agent_id)
        if not memory_path:
            # 三层降级：无文件 → 尝试全局 → 返回未声明
            global_path = os.path.expanduser("~/.openclaw/workspace/MEMORY.md")
            if os.path.exists(global_path):
                memory_path = global_path
            else:
                return "未声明目标（未找到 MEMORY.md，请配置 OPENCLAW_DATA_DIR 或 FLOW_MEMORY_MD_PATH）"
        
        current_mtime = os.path.getmtime(memory_path)
        now_str = datetime.now().isoformat()
        
        if not force_refresh:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "SELECT goals_text, source_mtime, expires_at FROM agent_goals WHERE agent_id=?",
                (agent_id,)
            )
            row = c.fetchone()
            conn.close()
            
            if row:
                goals_text, cached_mtime, expires_at = row
                if float(cached_mtime) == current_mtime and now_str < expires_at:
                    return goals_text
        
        with open(memory_path, "r", encoding="utf-8") as f:
            text = f.read()
        text = text[:1500] + ("..." if len(text) > 1500 else "")
        
        prompt = f"""阅读以下用户的长期记忆文件，提取活跃目标列表。

要求：
 - 只提取"当前正在推进"的目标，不要历史归档
 - 每个目标拆解为：目标名 + 实体（3-5个技术词/工具）+ 场景（2-3个工作场景）+ 里程碑（当前推进的具体任务，30字内）
 - 如无明确目标，返回"未声明目标"

输出格式（纯文本）：

目标1：[目标名]
   实体：[技术词1, 技术词2...]
   场景：[场景1, 场景2...]
   里程碑：[当前任务]

【文件内容】
 {text}
 """
        try:
            llm = self._get_llm()
            goals_text = llm.chat(prompt, max_tokens=800)
        except Exception as e:
            print(f"⚠️ GoalExtractor LLM 失败: {e}")
            return "未声明目标"
        
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO agent_goals (agent_id, goals_text, source_mtime, extracted_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_id, goals_text, current_mtime, now_str, expires))
        conn.commit()
        conn.close()
        
        return goals_text

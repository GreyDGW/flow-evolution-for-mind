"""
OpenClaw 数据目录跨平台发现模块
四级路径发现：环境变量 → 配置文件 → 自动探测 → 交互询问
"""

import os
from pathlib import Path
from typing import Optional, List


def find_openclaw_data_dir() -> Optional[Path]:
    """
    发现 OpenClaw 数据目录（agents 父目录）

    优先级：
    1. 环境变量 OPENCLAW_DATA_DIR
    2. 配置文件 ~/.flow_evolution/config
    3. 自动探测常见路径（跨平台）
    4. 返回 None（调用方需处理）
    """
    # 优先级1：环境变量
    env_path = os.environ.get("OPENCLAW_DATA_DIR")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists() and (p / "agents").exists():
            return p

    # 优先级2：配置文件（纯 key=value 格式，无 yaml 依赖）
    config_path = Path.home() / ".flow_evolution" / "config"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENCLAW_DATA_DIR="):
                        cfg_path = line.split("=", 1)[1].strip().strip('"').strip("'")
                        p = Path(cfg_path).expanduser()
                        if p.exists() and (p / "agents").exists():
                            return p
        except Exception:
            pass

    # 优先级3：自动探测（跨平台）
    candidates = [
        Path.home() / ".openclaw",  # Mac/Linux 默认
        Path.home() / "Library" / "Application Support" / "openclaw",  # Mac 系统目录
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "openclaw",  # Linux
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "openclaw",  # Windows
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "agents").exists():
            return candidate

    return None


def get_all_agent_jsonl_files() -> List[Path]:
    """获取所有 Agent 的标准 jsonl 文件（排除备份，递归扫描）"""
    openclaw_dir = find_openclaw_data_dir()
    if not openclaw_dir:
        raise RuntimeError(
            "未找到 OpenClaw 数据目录。\n"
            "解决方案：\n"
            "1. 设置环境变量：export OPENCLAW_DATA_DIR=/path/to/openclaw/data\n"
            "2. 或创建配置文件：mkdir -p ~/.flow_evolution && echo 'OPENCLAW_DATA_DIR=/path/to/openclaw/data' > ~/.flow_evolution/config\n"
            "3. 确认 OpenClaw 已安装且 agents 目录存在"
        )

    agents_dir = openclaw_dir / "agents"
    jsonl_files = []

    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        sessions_dir = agent_dir / "sessions"
        if not sessions_dir.exists():
            continue

        for f in sessions_dir.iterdir():
            if (f.is_file() and f.suffix == ".jsonl"
                and ".reset." not in f.name
                and ".checkpoint." not in f.name):
                jsonl_files.append(f)

    return sorted(jsonl_files)


def get_agent_jsonl_files(agent_id: Optional[str] = None) -> List[Path]:
    """获取指定 Agent 或所有 Agent 的标准 jsonl 文件"""
    openclaw_dir = find_openclaw_data_dir()
    if not openclaw_dir:
        raise RuntimeError("未找到 OpenClaw 数据目录")

    if agent_id:
        sessions_dir = openclaw_dir / "agents" / agent_id / "sessions"
        if not sessions_dir.exists():
            return []
        return sorted([
            f for f in sessions_dir.iterdir()
            if f.is_file() and f.suffix == ".jsonl"
            and ".reset." not in f.name
            and ".checkpoint." not in f.name
        ])

    return get_all_agent_jsonl_files()

"""
Flow Ecosystem 数据导入统一入口
"""
import os
from pathlib import Path
from importer.base_parser import import_jsonl_file

def import_jsonl(jsonl_path: str, db_path: str = "data/flow_ecosystem.db", agent_id: str = None):
    """一键导入 OpenClaw JSONL 到 sessions 表"""
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"JSONL 文件不存在: {jsonl_path}")
    return import_jsonl_file(Path(jsonl_path), Path(db_path))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python -m importer.pipeline <jsonl_path> [db_path]")
        sys.exit(1)
    import_jsonl(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/flow_ecosystem.db")

"""
实时文件监听模块：watchfiles 捕获 JSONL 修改，毫秒级增量导入
"""
import os
import time
import watchfiles
from watchfiles.main import Change
from importer.incremental import read_new_lines, import_batch, load_state, save_state

class JsonlWatcher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.state = load_state()
        self._last_event = {}
    
    def on_change(self, changes):
        for change, filepath in changes:
            if not filepath.endswith('.jsonl'):
                continue
            
            now = time.time()
            if filepath in self._last_event and now - self._last_event[filepath] < 2.0:  # 等待文件完全写入
                continue
            self._last_event[filepath] = now
            
            rel_path = os.path.relpath(filepath)
            last_pos = self.state.get(rel_path, 0)
            
            try:
                new_lines, new_pos = read_new_lines(filepath, last_pos)
                if new_lines:
                    from pathlib import Path
                    from importer.base_parser import _get_session_id_from_path
                    sid = _get_session_id_from_path(Path(filepath))
                    inserted = import_batch(new_lines, self.db_path, None, sid)
                    self.state[rel_path] = new_pos
                    save_state(self.state)
                    print(f"[实时] {os.path.basename(filepath)}: +{inserted} 条")
            except Exception as e:
                print(f"[实时] 失败: {e}")

def run_realtime_watcher(
    watch_dir: str = "~/.openclaw/agents",
    db_path: str = "data/flow_ecosystem.db"
):
    from importer.incremental import run_once
    
    watch_dir = os.path.expanduser(watch_dir)
    
    print("[实时] 先执行一次全量补齐...")
    run_once(watch_dir, db_path)
    
    watcher = JsonlWatcher(db_path)
    
    print(f"[实时] 监听已启动: {watch_dir}")
    print("[实时] 按 Ctrl+C 停止")
    
    print()
    
    for changes in watchfiles.watch(watch_dir):
        watcher.on_change(changes)

if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "data/flow_ecosystem.db"
    run_realtime_watcher(db_path=db)

import threading
import time
import sys
sys.path.insert(0, '.')

def run():
    from importer.watcher import run_realtime_watcher
    run_realtime_watcher(db_path='data/flow_ecosystem.db')

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(10)
print("\n10秒监听结束")

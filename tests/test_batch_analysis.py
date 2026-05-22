import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import path_setup

import sqlite3
import json
from collections import Counter
from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient
from plugin.state_distiller import StateDistiller

conn = sqlite3.connect("data/flow_ecosystem.db")
cursor = conn.cursor()
cursor.execute("SELECT sid, messages FROM semantic_sessions ORDER BY start_time DESC LIMIT 15")
rows = cursor.fetchall()
conn.close()

print("共读取 %d 条会话" % len(rows))

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)
distiller = StateDistiller(memory_path="MEMORY.md")

stats_labels = Counter()
stats_paces = Counter()
results = []

for idx, (sid, messages_json) in enumerate(rows):
    try:
        messages = json.loads(messages_json)
        recent = messages[-6:] if len(messages) > 6 else messages
        
        analysis = analyzer.analyze(recent, memory_path="MEMORY.md")
        if not analysis:
            print("[%d] 分析失败" % (idx+1))
            continue
        
        portrait = distiller.distill(analysis)
        stats_labels[portrait.label] += 1
        stats_paces[portrait.style.pace] += 1
        results.append(portrait.label)
        print("[%d/%d] %s pace=%s" % (idx+1, len(rows), portrait.label, portrait.style.pace))
    except Exception as e:
        print("[%d] 错误: %s" % (idx+1, str(e)[:50]))

print("\n=== 统计 ===")
print("成功: %d/%d 条" % (len(results), len(rows)))

if results:
    print("\n标签分布:")
    for label, cnt in stats_labels.most_common():
        print("  %s: %d 条" % (label, cnt))
    
    print("\npace 分布:")
    for pace, cnt in stats_paces.most_common():
        print("  %s: %d 条" % (pace, cnt))
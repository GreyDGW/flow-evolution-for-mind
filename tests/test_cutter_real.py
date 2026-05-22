import sys,os;sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))));import path_setup
import sqlite3,json
from collections import Counter
from plugin.session_analyzer import SessionAnalyzer,DeepSeekLLMClient

conn=sqlite3.connect('data/flow_ecosystem.db')
cursor=conn.cursor()

# 从 turns 表读取，按 interaction_id 分组
cursor.execute("SELECT interaction_id, user_message, assistant_response FROM turns ORDER BY interaction_id DESC LIMIT 200")
turns=cursor.fetchall()
conn.close()

print("="*60)
print("DeepSeek LLM 4维判定测试 (20条)")
print("="*60)

# 按 interaction_id 分组，组合成对话
interactions={}
for interaction_id, user_msg, assistant_msg in turns:
    if interaction_id not in interactions:
        interactions[interaction_id]=[]
    if user_msg:
        interactions[interaction_id].append({'role':'user','content':user_msg})
    if assistant_msg:
        interactions[interaction_id].append({'role':'assistant','content':assistant_msg})

interaction_list=list(interactions.items())[:20]

client=DeepSeekLLMClient()
analyzer=SessionAnalyzer(client)

stats={'total':0,'ok':0,'fail':0,'goals':Counter(),'closes':Counter(),'flows':Counter(),'cognitions':Counter()}

for i,(sid,messages) in enumerate(interaction_list,1):
    try:
        stats['total']+=1
        print("\n[%d/20] %s | %d轮"%(i,sid[:16],len(messages)))
        
        analysis=analyzer.analyze(messages,memory_path='MEMORY.md')
        if analysis:
            stats['ok']+=1
            stats['goals'][analysis.goal_alignment]+=1
            stats['closes'][analysis.closure_index]+=1
            stats['flows'][analysis.flow_depth]+=1
            stats['cognitions'][analysis.cognition_growth]+=1
            print("  ✅ g=%s c=%s f=%s cg=%s"%(analysis.goal_alignment,analysis.closure_index,analysis.flow_depth,analysis.cognition_growth))
        else:
            stats['fail']+=1
            print("  ❌ LLM分析失败")
            
    except Exception as e:
        print("  💥 %s"%str(e)[:80])
        stats['fail']+=1

print("\n"+"="*60)
print("统计报告")
print("="*60)
print("总数据: %d | 成功: %d | 失败: %d"%(stats['total'],stats['ok'],stats['fail']))
print("\n【目标对齐分布】")
for level,cnt in stats['goals'].most_common():
    print("  %s: %d (%.0f%%)"%(level,cnt,cnt/stats['total']*100 if stats['total'] else 0))
print("\n【闭环指数分布】")
for level,cnt in stats['closes'].most_common():
    print("  %s: %d (%.0f%%)"%(level,cnt,cnt/stats['total']*100 if stats['total'] else 0))
print("\n【心流深度分布】")
for level,cnt in stats['flows'].most_common():
    print("  %s: %d (%.0f%%)"%(level,cnt,cnt/stats['total']*100 if stats['total'] else 0))
print("\n【认知成长分布】")
for level,cnt in stats['cognitions'].most_common():
    print("  %s: %d (%.0f%%)"%(level,cnt,cnt/stats['total']*100 if stats['total'] else 0))

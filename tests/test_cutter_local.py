import sys,os;sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))));import path_setup
import sqlite3
from datetime import datetime
from plugin.session.session_cutter import SessionCutter

conn=sqlite3.connect('data/flow_ecosystem.db')
c=conn.cursor()

print("="*50)
print("Session Cutter 本地切割测试")
print("="*50)

# 直接从 turns 表读取，按 interaction_id 分组
c.execute("SELECT id, interaction_id, user_message, assistant_response, start_time FROM turns ORDER BY interaction_id, start_time LIMIT 200")
turns=c.fetchall()
conn.close()

# 按 interaction_id 分组
interactions={}
for tid,iid,um,am,ts in turns:
    if iid not in interactions:
        interactions[iid]=[]
    if um:
        interactions[iid].append({'role':'user','content':str(um),'timestamp':ts})
    if am:
        interactions[iid].append({'role':'assistant','content':str(am),'timestamp':ts})

print("共 %d 个 interactions" % len(interactions))

cutter=SessionCutter()
cut_count=0
no_cut=0
total_subs=0

interaction_list=list(interactions.items())[:30]

for i,(iid,msgs) in enumerate(interaction_list,1):
    if not msgs:
        continue
    
    # 逐turn调用cut_decision
    subs=[[]]
    prev=None
    for idx,m in enumerate(msgs):
        subs[-1].append(m)
        try:
            t=datetime.strptime(str(m['timestamp']),'%Y-%m-%d %H:%M:%S.%f')
            pt=datetime.strptime(str(prev['timestamp']),'%Y-%m-%d %H:%M:%S.%f') if prev else None
            r=cutter.cut_decision(
                current_turn_content=str(m['content']),
                current_turn_time=t,
                previous_turn_time=pt,
                previous_turn_content=str(prev['content']) if prev else None,
                session_goal=None,
                session_turn_count=idx
            )
            if hasattr(r,'cut') and r.cut and len(subs[-1])>1:
                subs.append([m])
                cut_count+=1
        except Exception as e:
            pass
        prev=m
    
    total_subs+=len(subs)
    if len(subs)==1:
        no_cut+=1
    
    # 打印详情
    print("\n[%d] %s: %d turns -> %d subs (cut:%s)"%(i,iid[:16],len(msgs),len(subs),'Y' if len(subs)>1 else 'N'))
    for j,sub in enumerate(subs,1):
        topics=[m['content'][:25] for m in sub[:2]]
        print("  [%d] %d轮: %s"%(j,len(sub),' | '.join(topics)))

print("\n"+"="*50)
print("统计: %d interactions | 切割%d次 | 未切割%d | 总子session%d"%(len(interaction_list),cut_count,no_cut,total_subs))
print("="*50)

import sys, os
from datetime import datetime
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session.session_cutter import SessionCutter, CutDecision

print("=== 端到端 Session Cutter 验证 ===")
cutter = SessionCutter()

conversation = [
    {'role': 'user', 'content': '帮我优化这个API的性能'},
    {'role': 'assistant', 'content': '建议用Redis缓存'},
    {'role': 'user', 'content': 'Redis怎么配置？'},
    {'role': 'user', 'content': '今天中午吃什么好？'},
    {'role': 'assistant', 'content': '红烧肉不错'},
]

sessions = []
current_session = []
previous_time = datetime.now()

for i, msg in enumerate(conversation):
    current_time = datetime.now()
    
    if i > 0:
        result = cutter.cut_decision(
            current_turn_content=msg['content'],
            current_turn_time=current_time,
            previous_turn_time=previous_time,
            previous_turn_content=conversation[i-1]['content']
        )
        print(f"消息[{i}]: {msg['content'][:20]}")
        print(f"   决策: {result.decision.value}")
        print(f"   原因: {result.reason}")
        print(f"   层级: {result.layer}")
        
        if result.decision == CutDecision.CUT:
            sessions.append(current_session.copy())
            current_session.clear()
            cutter.reset_session()
            print("   → 切割触发！")
    
    current_session.append(msg)
    previous_time = current_time

if current_session:
    sessions.append(current_session)

print("\n=== 最终结果 ===")
print(f"总 Session 数: {len(sessions)}")
for i, s in enumerate(sessions):
    topics = [m['content'][:25] for m in s]
    print(f"Session {i+1}: {topics}")

if len(sessions) == 2:
    print("\n🎉 端到端验证通过：正确切割为 2 个 Session")
else:
    print(f"\n⚠️ 预期 2 个 Session，实际 {len(sessions)} 个")
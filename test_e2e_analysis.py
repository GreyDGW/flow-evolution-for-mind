#!/usr/bin/env python3
import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

SID = "7d899182-b2e3-4bda-ab5b-3933282fcc7b"

print("=" * 70)
print("=== 端到端验证：目标感知认知分析 ===")
print("=" * 70)
print(f"\n📋 测试 Session ID: {SID}")

# 1. 读取消息
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()
c.execute('''
    SELECT role, content_text, timestamp, agent_id 
    FROM sessions 
    WHERE session_id = ? 
    AND role IN ('user','assistant') 
    AND (is_system_noise = 0 OR is_system_noise IS NULL) 
    AND (is_auto_push = 0 OR is_auto_push IS NULL) 
    ORDER BY timestamp
''', (SID,))
rows = c.fetchall()
conn.close()

msgs = [{'role': r[0], 'content': r[1], 'timestamp': r[2]} for r in rows]
agent_id = rows[0][3] if rows else None

print(f"📊 消息数: {len(msgs)}")
print(f"🤖 Agent ID: {agent_id}")
print("\n📝 对话预览（前 5 条）:")
print("-" * 70)
for i, m in enumerate(msgs[:5], 1):
    content_preview = m['content'][:60] + "..." if len(m['content']) > 60 else m['content']
    print(f"{i}. [{m['role']:9}] {content_preview}")
if len(msgs) > 5:
    print(f"... 共 {len(msgs)} 条消息")

# 2. 分析
print("\n" + "=" * 70)
print("🚀 开始分析（含 goals_text 注入）")
print("=" * 70)

llm = DeepSeekLLMClient()
analyzer = SessionAnalyzer(llm)

try:
    result = analyzer.analyze(msgs, session_id=SID, agent_id=agent_id)
    
    if result:
        print("\n✅ 分析成功！四维评估结果:")
        print("-" * 70)
        
        print(f"\n🎯 目标对齐度 (Goal Alignment):   {result.goal_alignment}")
        if hasattr(result, 'goal_evidence') and result.goal_evidence:
            evidence = result.goal_evidence
            print(f"   📎 证据 ({len(evidence)} 字符):")
            # 高亮显示前 300 字符，便于检查是否引用了实际目标
            print("   ┌" + "─" * 66)
            for line in evidence[:350].split('\n'):
                display_line = line if len(line) <= 68 else line[:67] + "..."
                print("   │" + display_line)
            if len(evidence) > 350:
                print("   │... (共 {} 字符)".format(len(evidence)))
                print("   └" + "─" * 66)
        
        print(f"\n🔄 闭环指数 (Closure Index):     {result.closure_index}")
        if hasattr(result, 'closure_evidence') and result.closure_evidence:
            print(f"   📎 证据: {result.closure_evidence[:150]}...")
        
        print(f"\n🌊 心流深度 (Flow Depth):       {result.flow_depth}")
        if hasattr(result, 'flow_evidence') and result.flow_evidence:
            print(f"   📎 证据: {result.flow_evidence[:150]}...")
        
        print(f"\n🧠 认知成长 (Cognition Growth):  {result.cognition_growth}")
        if hasattr(result, 'cognition_evidence') and result.cognition_evidence:
            print(f"   📎 证据: {result.cognition_evidence[:150]}...")
        
        print("\n" + "=" * 70)
        print("🔍 验证要点:")
        print("-" * 70)
        print("✅ goals_text 是否注入 Prompt? → 检查上方 '目标对齐度' 证据是否引用具体目标")
        print("✅ 是否引用了 newness 的实际任务? → 应包含 'Flow Ecosystem', 'v1.0', 'Graphiti' 等关键词")
        print("✅ 其他维度是否正常? → 闭环/心流/成长应独立于目标进行评估")
        print("=" * 70)
        
    else:
        print("❌ 分析失败 - 返回 None")
        
except Exception as e:
    print(f"\n❌ 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 验证完成!")

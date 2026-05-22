import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient
import re

conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

c.execute("""
    SELECT DISTINCT session_id
    FROM sessions
    WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
""")
sessions = [r[0] for r in c.fetchall()]
print(f"4/20 session数: {len(sessions)}")

llm = DeepSeekLLMClient()

# 临时禁用校验，查看原始输出
analyzer = SessionAnalyzer(llm_client=llm)

for sid in sessions[:2]:
    c.execute("SELECT role, content_text FROM sessions WHERE session_id = ? ORDER BY timestamp", (sid,))
    messages = [{'role': r, 'content': t or ''} for r, t in c.fetchall()]
    
    # 直接调用parse_response查看原始输出
    dialog_text = analyzer._format_messages(messages)
    prompt = f"{analyzer.PROMPT_TEMPLATE}\n\n对话原文：\n{dialog_text}"
    response = llm.chat(prompt)
    
    print(f"\n{'='*60}")
    print(f"Session: {sid[:16]}...")
    print(f"{'='*60}")
    print(f"原始响应前500字:\n{response[:500]}...")
    print(f"\n响应末尾30字: '{response[-30:]}'")
    
    # 检查末尾字符
    matches = re.findall(r'(目标感|闭环感|沉浸感|成长感)[：:]\s*\[?([高中低])\]?\s*[,，]?\s*证据[：:]\s*\[?([^\]\n]+)\]?', response)
    print(f"\n解析到 {len(matches)} 个维度")
    for m in matches:
        ev = m[2].strip()
        is_complete = bool(re.search(r'[。！？."\"]$', ev))
        print(f"  {m[0]}: {m[1]} | 长度={len(ev)} | 完整={is_complete} | 末尾='{ev[-15:]}'")

conn.close()
import os
import re

# 需要更新的文件列表
files_to_update = [
    'reanalyze.py',
    'reanalyze_v82.py',
    'reanalyze_v82_clean.py',
    'reanalyze_v83.py',
    'reanalyze_v84.py',
    'reanalyze_v85.py',
    'complete_420.py',
]

# 旧的 REPLACE INTO 模式
old_sql_pattern = r"""REPLACE INTO session_analyses\s*\(
\s*session_id,\s*goal_alignment,\s*closure_index,\s*flow_depth,\s*cognition_growth,
\s*goal_evidence,\s*closure_evidence,\s*flow_evidence,\s*cognition_evidence,
\s*llm_model,\s*llm_latency_ms,\s*prompt_version\)
\s*VALUES \(\?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?\)"""

# 新的 REPLACE INTO 模式（包含 portrait 和 style 字段）
new_sql = """REPLACE INTO session_analyses
                (session_id, goal_alignment, closure_index, flow_depth, cognition_growth,
                 goal_evidence, closure_evidence, flow_evidence, cognition_evidence,
                 llm_model, llm_latency_ms, prompt_version,
                 portrait_label, portrait_description, portrait_suggestion, portrait_rule_insight,
                 style_pace, style_depth, style_tone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

# 旧的 values 列表模式
old_values_pattern = r'(\(.*?result\.cognition_growth,\s*\n\s*\'deepseek-chat\',\s*0,\s*\'v8\.5\'\)'

# 新的 values 列表模式（追加 portrait 和 style 字段）
new_values = r"""\1
                # Portrait & Style 字段
                result.portrait_label or '平稳推进',
                result.portrait_description or '状态平稳，保持观察',
                result.portrait_suggestion or '保持当前节奏',
                result.portrait_rule_insight or '状态组合未命中明确规则，保持观察',
                result.style_pace or 'explore',
                result.style_depth or 'deep',
                result.style_tone or 'neutral'
            )"""

for filename in files_to_update:
    if not os.path.exists(filename):
        print(f"⚠️ 跳过: {filename} (不存在)")
        continue
    
    with open(filename, 'r') as f:
        content = f.read()
    
    if 'portrait_label' in content:
        print(f"✅ 跳过: {filename} (已包含 portrait 字段)")
        continue
    
    if 'REPLACE INTO session_analyses' in content:
        # 替换 SQL 部分
        new_content = re.sub(old_sql_pattern, new_sql, content, flags=re.DOTALL | re.VERBOSE)
        
        if new_content != content:
            # 替换 values 部分
            new_content = re.sub(old_values_pattern, new_values, new_content, flags=re.DOTALL | re.VERBOSE)
            
            with open(filename, 'w') as f:
                f.write(new_content)
            print(f"✅ 已更新: {filename}")
        else:
            print(f"⚠️ 未找到匹配的SQL模式: {filename}")
    else:
        print(f"ℹ️ 无需更新: {filename} (无 REPLACE INTO)")

print("\n完成！")
import sqlite3
import sys
sys.path.insert(0, '.')
from plugin.state_distiller import StateDistiller

DB_PATH = 'data/flow_ecosystem.db'

def backfill():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 找出 v8.5 且 portrait 为 NULL 的记录
    c.execute("""
        SELECT id, session_id, goal_alignment, closure_index, flow_depth, cognition_growth
        FROM session_analyses
        WHERE prompt_version = 'v8.5'
        AND (portrait_label IS NULL OR style_pace IS NULL)
    """)
    rows = c.fetchall()
    
    if not rows:
        print("✅ 没有需要回填的 v8.5 记录")
        conn.close()
        return
    
    distiller = StateDistiller()
    updated = 0
    
    for row in rows:
        id_, session_id, g, cl, f, cg = row
        try:
            portrait = distiller.distill(g, cl, f, cg)
            if not portrait:
                print(f"⚠️ ID={id_} distill 返回空，跳过")
                continue
            
            c.execute("""
                UPDATE session_analyses
                SET portrait_label = ?,
                    portrait_description = ?,
                    portrait_suggestion = ?,
                    portrait_rule_insight = ?,
                    style_pace = ?,
                    style_depth = ?,
                    style_tone = ?
                WHERE id = ?
            """, (
                portrait.label,
                portrait.description,
                portrait.suggestion,
                portrait.rule_insight,
                portrait.style_pace,
                portrait.style_depth,
                portrait.style_tone,
                id_
            ))
            updated += 1
            print(f"✅ ID={id_} | session={session_id[:16]}... | portrait={portrait.label} | pace={portrait.style_pace}")
        except Exception as e:
            print(f"❌ ID={id_} 回填失败: {e}")
    
    conn.commit()
    conn.close()
    print(f"\n🎉 回填完成：{updated}/{len(rows)} 条记录已修复")

if __name__ == '__main__':
    backfill()
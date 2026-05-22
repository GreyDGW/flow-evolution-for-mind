import sqlite3
import json
from datetime import datetime
from src.openclaw_flow_plugin.core.llm_manager import LLMManager

def update_goals_with_llm():
    print("=" * 70)
    print("🧠 使用Llama-3.2-1B更新目标数据库")
    print("=" * 70)

    llm = LLMManager()
    print(f"\n✅ LLM初始化成功")
    print(f"   - 模型: {llm.model_name}")
    print(f"   - 使用模拟模式: {llm.use_mock}")

    db_path = 'flow_ecosystem.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n📊 获取用户消息...")
    cursor.execute("""
        SELECT id, timestamp, content_text
        FROM sessions
        WHERE role='user'
        AND content_text IS NOT NULL
        AND content_text != ''
        AND content_text NOT LIKE '%[Bootstrap%'
        AND content_text NOT LIKE '%FlowGuard%'
        AND content_text NOT LIKE '| %'
        AND LENGTH(content_text) > 10
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    messages = cursor.fetchall()
    print(f"   获取到 {len(messages)} 条用户消息")

    processed = 0
    added_goals = 0

    print("\n🔄 开始处理消息...")
    for msg_id, timestamp, content in messages:
        try:
            result = llm.extract_goals(content)

            if result and 'goals' in result and result['goals']:
                for goal_text in result['goals']:
                    if '```' in goal_text or 'json' in goal_text.lower():
                        continue
                    if '"goals"' in goal_text or '"time_horizon"' in goal_text:
                        continue

                    goal_text = goal_text.strip()
                    if len(goal_text) < 5:
                        continue

                    time_horizon = result.get('time_horizon', ['short'])[0] if result.get('time_horizon') else 'short'

                    cursor.execute("""
                        INSERT INTO goals (declared_text, declared_at, status, drift_score, last_mentioned, complexity_score, time_horizon, completion_score)
                        VALUES (?, ?, 'active', 0.0, ?, 0.0, ?, 0.0)
                    """, (goal_text, timestamp, datetime.now(), time_horizon))

                    added_goals += 1
                    print(f"   ✅ [{msg_id}] 添加目标: {goal_text[:50]}...")

            processed += 1
            print(f"   📝 [{processed}/{len(messages)}] 已处理")

        except Exception as e:
            print(f"   ⚠️ 处理消息 {msg_id} 时出错: {e}")
            continue

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM goals WHERE status='active'")
    total_goals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM goals WHERE status='closed'")
    closed_goals = cursor.fetchone()[0]

    print("\n" + "=" * 70)
    print("📊 更新结果统计")
    print("=" * 70)
    print(f"   处理消息数: {processed}")
    print(f"   新增目标数: {added_goals}")
    print(f"   活跃目标总数: {total_goals}")
    print(f"   已关闭目标: {closed_goals}")

    print("\n📋 最近添加的目标:")
    cursor.execute("""
        SELECT id, declared_text, time_horizon, declared_at
        FROM goals
        ORDER BY id DESC
        LIMIT 10
    """)
    recent_goals = cursor.fetchall()
    for goal_id, text, horizon, declared_at in recent_goals:
        print(f"   [{goal_id}] {horizon}: {text[:40]}...")

    conn.close()
    print("\n✅ 更新完成！")

if __name__ == '__main__':
    update_goals_with_llm()
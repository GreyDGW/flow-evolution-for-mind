import path_setup
#!/usr/bin/env python3
"""
完整流水线测试：preprocessor → 向量切分 → LLM分析 → 闭环分析
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.session import TurnPreprocessor, VectorLayer, create_embedder
from src.core import OpenClawLLMClient, get_llm_config
from src.session import ClosureAnalyzer


def test_full_pipeline():
    test_cases = [
        {
            "name": "完整PDCA+高心流",
            "messages": [
                {"role": "user", "content": "我打算把单体应用拆成微服务，计划先拆用户服务和订单服务，用DDD划分边界"},
                {"role": "assistant", "content": "好的，建议先画领域图"},
                {"role": "user", "content": "我画完了领域图，代码也改了，测试QPS提升30%，文档写好了"},
            ]
        },
        {
            "name": "部分PDCA缺Adjust",
            "messages": [
                {"role": "user", "content": "我想加缓存"},
                {"role": "assistant", "content": "可以"},
                {"role": "user", "content": "加了缓存，测试通过"},
            ]
        },
        {
            "name": "无PDCA纯闲聊",
            "messages": [
                {"role": "user", "content": "今天天气不错"},
                {"role": "assistant", "content": "是啊"},
                {"role": "user", "content": "晚饭吃什么"},
            ]
        },
        {
            "name": "目标漂移",
            "messages": [
                {"role": "user", "content": "我在研究微服务架构"},
                {"role": "assistant", "content": "好的"},
                {"role": "user", "content": "突然想写首诗"},
            ]
        },
        {
            "name": "高心流+质疑AI",
            "messages": [
                {"role": "user", "content": "你说的不对，我重新分析这个问题"},
                {"role": "assistant", "content": "请说"},
                {"role": "user", "content": "我觉得应该用不同的方案，验证通过后调整架构"},
            ]
        },
        {
            "name": "复杂代码+PDCA",
            "messages": [
                {"role": "user", "content": "计划优化数据库查询性能```sql\nSELECT * FROM orders WHERE user_id=1\n```"},
                {"role": "assistant", "content": "可以加索引"},
                {"role": "user", "content": "我加了索引，测试通过，文档更新了"},
            ]
        },
        {
            "name": "多轮规划",
            "messages": [
                {"role": "user", "content": "我想重构这个模块，计划分三步走"},
                {"role": "assistant", "content": "说说计划"},
                {"role": "user", "content": "第一步完成，重构了数据层"},
                {"role": "assistant", "content": "好"},
                {"role": "user", "content": "第二步完成，接口也改了，测试通过"},
            ]
        },
        {
            "name": "短消息低价值",
            "messages": [
                {"role": "user", "content": "好"},
                {"role": "assistant", "content": "好的"},
                {"role": "user", "content": "嗯"},
            ]
        },
        {
            "name": "跨域知识迁移",
            "messages": [
                {"role": "user", "content": "我把前端响应式设计的思想用到后端API了，参考了微服务模式"},
                {"role": "assistant", "content": "有意思"},
                {"role": "user", "content": "测试通过，性能提升20%"},
            ]
        },
        {
            "name": "情绪硬信号+调整",
            "messages": [
                {"role": "user", "content": "之前方案有问题，我重新想了下"},
                {"role": "assistant", "content": "什么问题"},
                {"role": "user", "content": "数据一致性问题，我调整了策略，重新实现，测试验证通过，文档也更新了"},
            ]
        },
    ]

    print("=" * 70)
    print("完整流水线测试")
    print("=" * 70)

    preprocessor = TurnPreprocessor()
    embedder = create_embedder()
    config = get_llm_config()
    llm_client = OpenClawLLMClient(config["api_key"], config["base_url"], config["model"])
    analyzer = ClosureAnalyzer(llm_client)

    active_goals = [{"text": "成为架构师", "type": "长期", "status": "推进中"}]

    results = []

    for idx, case in enumerate(test_cases, 1):
        print(f"\n【{idx}/10】{case['name']}")
        print(f"  原始消息: {len(case['messages'])} 轮")

        # [1] Preprocessor 清洗
        cleaned = []
        for msg in case["messages"]:
            result = preprocessor.preprocess(msg.get("content", ""))
            cleaned.append({
                "role": msg.get("role", "user"),
                "content": result.get("embedding_text", msg.get("content", "")),
                "has_code": result.get("has_code", False),
                "code_hashes": result.get("code_hashes", []),
            })
        print(f"  清洗后: {len(cleaned)} 轮")

        # [2] 向量分析（简单相似度检测）
        vector_layer = VectorLayer(embedder)
        vectors = []
        for msg in cleaned:
            v = vector_layer.add_turn(msg.get("content", ""))
            if v:
                vectors.append(v)

        if len(vectors) >= 2:
            avg_sim = sum(
                vector_layer.compute_similarity(vectors[i], vectors[i+1])
                for i in range(len(vectors)-1)
            ) / (len(vectors) - 1)
            print(f"  向量相似度: {avg_sim:.3f}")

        # [3] LLM + ClosureAnalyzer 分析
        try:
            result = analyzer.analyze_session(cleaned, active_goals)
            ewci = result.get("ewci", 0)
            flow = result.get("flow_depth", 0)
            progress = result.get("goal_alignment", {}).get("goal_progress", 0)
            drift = result.get("goal_alignment", {}).get("drift_score", 0)
            completeness = result.get("completeness", 0)

            print(f"  ✅ EWCI: {ewci:.1f} | 心流: {flow:.1f} | 推进: {progress} | 漂移: {drift:.2f}")
            print(f"     完整度: {completeness:.0f}")

            pdca = result.get("pdca", {})
            stages = ["plan", "do", "check", "adjust"]
            pd = [pdca.get(s, {}).get("detected", False) for s in stages]
            print(f"     PDCA: {pd}")

            if result.get("_error"):
                print(f"     ⚠️ {result['_error'][:50]}")

            results.append({
                "name": case["name"],
                "ewci": ewci,
                "flow": flow,
                "progress": progress,
                "drift": drift,
                "completeness": completeness,
                "pdca": pd,
                "error": result.get("_error")
            })
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results.append({"name": case["name"], "ewci": 0, "error": str(e)})

    # 汇总报告
    print("\n" + "=" * 70)
    print("汇总报告")
    print("=" * 70)
    print(f"{'场景':<20} | {'EWCI':>6} | {'心流':>6} | {'推进':>4} | {'漂移':>5} | {'PDCA'}")
    print("-" * 70)

    for r in results:
        if "error" in r and r["error"]:
            print(f"{r['name']:<20} | ❌")
        else:
            pd_str = "".join(["✅" if p else "❌" for p in r.get("pdca", [])])
            print(f"{r['name']:<20} | {r['ewci']:>6.1f} | {r['flow']:>6.1f} | {r['progress']:>4} | {r['drift']:>5.2f} | {pd_str}")

    success = sum(1 for r in results if "error" not in r or not r.get("error"))
    print(f"\n成功率: {success}/{len(results)} ({success/len(results)*100:.0f}%)")

    if success == len(results):
        print("🎉 全部通过!")
    else:
        print(f"⚠️ {len(results) - success} 个场景有问题")


if __name__ == "__main__":
    test_full_pipeline()
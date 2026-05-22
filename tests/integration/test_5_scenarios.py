import path_setup
"""5场景验证测试"""
import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin')

from src.session import SessionCutter

def run_test():
    cutter = SessionCutter(llm_client=None, embedder=None)

    print("=== 场景5: sim=0.30+turn<10+正常内容 ===")
    cutter5 = SessionCutter(llm_client=None, embedder=None)
    for i in range(2):
        cutter5._vector_layer.add_turn(f"正常对话{i}")
    r5 = cutter5._vector_layer.decide("关于刚才那个接口，我再确认下参数")
    print(f"内容: '关于刚才那个接口，我再确认下参数'")
    print(f"决策: {r5[0].value}, 理由: {r5[1]}")
    print(f"LLM触发: {r5[2].get('triggered', 'N/A')}")

    # 关键断言：场景5绝不触发LLM
    assert r5[2].get('triggered') == False, f"场景5绝不触发LLM, 得到{r5[2]}"
    print("\n✅ 断言通过: 场景5绝不触发LLM")

    # 检查内容是否包含"摆烂"
    print(f"\n检查'摆烂'关键词: {'摆烂' in '关于刚才那个接口，我再确认下参数'}")
    print(f"检查'算了'关键词: {'算了' in '关于刚才那个接口，我再确认下参数'}")

if __name__ == "__main__":
    run_test()

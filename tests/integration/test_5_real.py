import path_setup
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin')

from src.session import VectorLayer
from plugin.session.embedding import create_embedder

embedder = create_embedder()

def run_scenario(name, history, new_turn):
    vl = VectorLayer(embedder=embedder)
    for h in history:
        vl.add_turn(h)
    r = vl.decide(new_turn)
    sim = r[2].get('similarity', 0)
    decision = r[0].value
    triggered = r[2].get('triggered', 'N/A')
    print(f"{name}: sim={sim:.2f} decision={decision} triggered={triggered}")
    return r

print("=== 5场景测试 ===\n")
r1 = run_scenario("场景1 同主题", ["微服务讨论", "服务边界", "DDD领域模型"], "数据一致性方案")
r2 = run_scenario("场景2 切换话题", ["微服务通信", "服务治理", "负载均衡"], "今天天气不错")
r3 = run_scenario("场景3 12Turn+漂移", ["微服务"]*12, "天气真好")
r4 = run_scenario("场景4 5Turn+摆烂", ["工作内容"]*5, "算了摆烂不想干")
r5 = run_scenario("场景5 5Turn+正常", ["工作讨论"]*5, "关于接口参数确认")

print("\n=== 断言验证 ===")
s1 = "PASS" if r1[2].get('similarity', 0) > 0.4 else "FAIL"
s2 = "PASS" if r2[2].get('similarity', 0) < 0.15 else "SIM"
s5 = "PASS" if r5[2].get('triggered') == False else "FAIL"
print(f"场景1 sim > 0.4: {s1}")
print(f"场景2 sim < 0.15: {s2}")
print(f"场景5 不触发LLM: {s5}")

"""Simple test script to verify core algorithms."""

import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/src')

from openclaw_flow_plugin.core.navigation import calculate_navigation_raw, navigation_to_percent
from openclaw_flow_plugin.core.power import calculate_power
from openclaw_flow_plugin.core.strategic_index import calculate_strategic_index
from openclaw_flow_plugin.core.type_matcher import match_type
from openclaw_flow_plugin.core.report_generator import generate_five_dimension_table, generate_type_determination
from openclaw_flow_plugin.core.models import CoreInputs

print("=" * 60)
print("Flow Ecosystem Skill - Core Algorithm Tests")
print("=" * 60)

# Test Navigation calculation
print("\n1. Navigation系数计算测试")
nav_raw = calculate_navigation_raw(80, 20)
nav_percent = navigation_to_percent(nav_raw)
print(f"   目标拟合度=80%, 漂移率=20%")
print(f"   Navigation原始值: {nav_raw:.4f} (预期: 0.28)")
print(f"   Navigation百分制: {nav_percent:.1f} (预期: 64)")
assert abs(nav_raw - 0.28) < 0.001, f"Navigation原始值错误: {nav_raw}"
assert abs(nav_percent - 64) < 0.1, f"Navigation百分制错误: {nav_percent}"
print("   ✓ 通过")

# Test Power calculation
print("\n2. Power能力动能计算测试")
power = calculate_power(80, 70, 90)
print(f"   心流指数=80, 认知进化=70, EWCI=90")
print(f"   Power: {power:.1f} (预期: 81.5)")
assert abs(power - 81.5) < 0.1, f"Power计算错误: {power}"
print("   ✓ 通过")

# Test Strategic Index (gated model)
print("\n3. 综合指数门控模型测试")
inputs = CoreInputs(
    flow_index=80,
    cognitive_evolution_index=70,
    ewci=90,
    achievement_fit=80,
    drift_rate=20
)
result = calculate_strategic_index(inputs)
print(f"   Power=80, Navigation=0.5")
print(f"   综合指数: {result.strategic_index:.1f} (预期: 22.8)")
assert abs(result.strategic_index - 22.8) < 0.1, f"综合指数错误: {result.strategic_index}"

# Test gated model with negative navigation
inputs2 = CoreInputs(
    flow_index=80,
    cognitive_evolution_index=70,
    ewci=90,
    achievement_fit=30,
    drift_rate=80
)
result2 = calculate_strategic_index(inputs2)
print(f"   Power=80, Navigation=-0.2 (方向错误)")
print(f"   综合指数: {result2.strategic_index:.1f} (预期: 0)")
assert result2.strategic_index == 0, f"门控逻辑错误: {result2.strategic_index}"
print("   ✓ 通过")

# Test 12-type combination matching
print("\n4. 12型核心组合表匹配测试")
matched = match_type(80, 70, 65, 75, 80)
print(f"   Navigation=80, 目标拟合度=70, EWCI=65, 心流=75, 认知进化=80")
print(f"   匹配类型: {matched['name']} (预期: 战略清晰型)")
assert matched['name'] == '战略清晰型', f"类型匹配错误: {matched['name']}"
print("   ✓ 通过")

# Test Navigation < 50 special case
matched2 = match_type(40, 80, 80, 80, 80)
print(f"   Navigation=40 (<50), 其他维度=80")
print(f"   匹配类型: {matched2['name']} (预期: 勤奋破坏型)")
assert matched2['name'] == '勤奋破坏型', f"Navigation<50处理错误: {matched2['name']}"
print("   ✓ 通过")

# Test five-dimensional table generation
print("\n5. 五维评估表格生成测试")
table = generate_five_dimension_table(80, 75, 70, 65, 85)
print("   生成的表格包含5个维度:")
for row in table:
    print(f"     - {row['维度']}: {row['数值']}分, {row['快速判定']}, {row['详细层级']}")
assert len(table) == 5, f"表格维度数量错误: {len(table)}"
print("   ✓ 通过")

# Test type determination generation
print("\n6. 类型判定输出测试")
type_result = generate_type_determination(80, 75, 70, 65, 85, 75, 60)
print(f"   类型名称: {type_result['type_name']}")
print(f"   Navigation: {type_result['navigation']['value']:.1f} ({type_result['navigation']['icon']} {type_result['navigation']['level']})")
print(f"   Power: {type_result['power']:.1f}")
print(f"   综合指数: {type_result['strategic_index']:.1f} ({type_result['strategic_icon']} {type_result['strategic_level']})")
print("   ✓ 通过")

print("\n" + "=" * 60)
print("所有核心算法测试通过！")
print("=" * 60)
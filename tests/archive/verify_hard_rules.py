import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session.session_cutter import HardRulesLayer, CutDecision
from datetime import datetime, timedelta
import time

rules = HardRulesLayer()

# 场景A：正常延续（<30分钟，无切割信号）
now = datetime.now()
recent = now - timedelta(minutes=10)
result = rules.check("帮我优化API性能", recent, now, False, False)
print("场景A（正常延续）:", result[0], result[1])

# 场景B：超时（>30分钟）
old = now - timedelta(hours=1)
result = rules.check("换个话题", old, now, False, False)
print("场景B（超时1小时）:", result[0], result[1])

# 场景C：显式命令
result = rules.check("/new 开启新会话", now, now, False, False)
print("场景C（显式切割）:", result[0], result[1])

# 场景D：短消息豁免
result = rules.check("好的", now, now, False, False)
print("场景D（短消息豁免）:", result[0], result[1])

print("\n验证 1: 硬规则测试完成")
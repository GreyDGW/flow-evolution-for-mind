import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session.session_cutter import SessionCutter
from plugin.session.preprocessor import TurnPreprocessor
import time

cutter = SessionCutter()
preprocessor = TurnPreprocessor()

messages_a = [
    {"role": "user", "content": "帮我优化这个API的性能", "timestamp": time.time()},
    {"role": "assistant", "content": "建议用Redis缓存", "timestamp": time.time() + 10},
    {"role": "user", "content": "Redis怎么配置？", "timestamp": time.time() + 20},
]
result_a = cutter.should_cut(messages_a)
print("场景A（正常延续）: 切割=" + str(result_a.cut) + " | 原因=" + str(result_a.reason))
assert not result_a.cut, "正常对话不应切割"

messages_b = [
    {"role": "user", "content": "早上好", "timestamp": time.time() - 3600},
    {"role": "assistant", "content": "早上好", "timestamp": time.time() - 3600 + 5},
    {"role": "user", "content": "现在说点别的", "timestamp": time.time()},
]
result_b = cutter.should_cut(messages_b)
print("场景B（超时1小时）: 切割=" + str(result_b.cut) + " | 原因=" + str(result_b.reason))
assert result_b.cut, "超时应切割"

messages_c = [
    {"role": "user", "content": "我们换个话题吧", "timestamp": time.time()},
    {"role": "assistant", "content": "好的，你想聊什么？", "timestamp": time.time() + 5},
]
result_c = cutter.should_cut(messages_c)
print("场景C（显式换话题）: 切割=" + str(result_c.cut) + " | 原因=" + str(result_c.reason))
assert result_c.cut, "显式切割信号应触发"

messages_d = [
    {"role": "user", "content": "看看这段代码\n```python\nprint(1)\n```\n有问题吗？"},
    {"role": "assistant", "content": "没问题。再看看这个引用\n> 这是引用块\n> 第二行\n理解了吗？"},
]
result_d = cutter.should_cut(messages_d)
print("场景D（代码块/引用块）: 切割=" + str(result_d.cut) + " | 原因=" + str(result_d.reason))

print("\n🎉 验证 1 通过：硬规则切割逻辑正常")
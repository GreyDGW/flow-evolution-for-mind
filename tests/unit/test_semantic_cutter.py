import path_setup
#!/usr/bin/env python3
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.session import SemanticSessionCutter

msgs = [
    {'role':'user','content':'我打算把单体应用拆成微服务，计划先拆用户服务和订单服务'},
    {'role':'assistant','content':'好的，建议先画领域图'},
    {'role':'user','content':'我画完了领域图，代码也改了，测试QPS提升30%'},
    {'role':'user','content':'中午吃什么好？附近有什么推荐'},
    {'role':'assistant','content':'楼下新开了一家川菜馆，水煮鱼不错'},
    {'role':'user','content':'刚才的拆分方案还需要加熔断机制，我研究了下Sentinel'},
    {'role':'assistant','content':'Sentinel比Hystrix更轻量'},
    {'role':'user','content':'我配好了降级策略，文档更新了'},
    {'role':'user','content':'下午要不要喝杯咖啡提提神'},
    {'role':'assistant','content':'好啊，楼下星巴克还是瑞幸'},
    {'role':'user','content':'微服务的监控方案还没定，Prometheus+Grafana怎么样'},
    {'role':'assistant','content':'这套组合是云原生标准'},
    {'role':'user','content':'我配好了Prometheus采集，Grafana仪表盘也搭好了'},
]

cutter = SemanticSessionCutter()
sessions = cutter.cut_sessions(msgs, threshold=0.15)
stats = cutter.get_stats(sessions)

print(f'切分: {stats["session_count"]} 个 Session')
for idx, s in enumerate(sessions):
    print(f'  S{idx+1}: {len(s)}轮 | {s[0]["content"][:25]}...')

print(f'\n统计: 总消息{stats["total_messages"]} | 平均长度{stats["avg_session_length"]:.1f}')
print('✅ SessionCutter 固化成功')
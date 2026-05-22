# OpenClaw Flow Plugin (Scaffold)

这是一个基于 `Flow_Ecosystem_Skill_PRD_V6.1` 搭建的 Python 插件基础框架。

当前已提供：

- 核心战略层：`Power / Navigation / 综合指数`
- 心流指数链路：片段时长、基础质量分、信号增益、时间系数、日心流指数
- 目标拟合度：分层加权与漂移率
- 执行层 EWCI：E/N/Q 计算与零闭环保护
- 认知进化指数：当日质量、跨日稳定、效率奖赏
- 生物层基础：Fatigue Guard 与 T0 观测窗口
- 插件统一入口：`run_plugin`（简版）+ `run_full_plugin`（整合版）

说明：

- 目前是“可运行的基础版”，优先保证公式主干可落地、模块边界清晰。
- 高阶细则（例如四问闭环细粒度规则、Ghost 模式权限锁定状态机）可在此基础上继续扩展。

import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { registerCounterHook } from "./hooks/counter.js";
import { registerInjectorHook } from "./hooks/injector.js";

export default definePluginEntry({
  id: "flow-style-plugin",
  name: "Flow Style Tuner",
  description: "Cognitive style monitoring and injection",
  kind: "utility",
  register(api) {
    registerCounterHook(api);
    registerInjectorHook(api);
    api.logger.info("[flow-style] Plugin loaded successfully");

    // ===== FLOW_REPORT_INTERCEPT =====
    // P0: 所有 Agent 的 /flow 统一走深度报告，禁止 LLM 摘要
    api.on('before_prompt_build', async (context) => {
      const { messages } = context;
      const lastUserMsg = messages && messages.length > 0 ?
        messages.filter(m => m.role === 'user').pop() : null;

      if (lastUserMsg && lastUserMsg.content &&
        (lastUserMsg.content.trim().startsWith('/flow') ||
         (lastUserMsg.content.trim().includes('报告') && lastUserMsg.content.trim().includes('flow')))) {

        try {
          const { execSync } = require('child_process');
          const today = new Date().toISOString().slice(0, 10);
          const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);

          const report = execSync(
            'cd "/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin" && ' +
            'python3 -c "import sys; sys.path.insert(0, \\".\"); ' +
            'from plugin.deep_report_final import DeepReportFinal; ' +
            'drf = DeepReportFinal(); ' +
            'print(drf.generate(\'' + today + '\', \'' + tomorrow + '\'))"',
            { encoding: 'utf-8', timeout: 45000, maxBuffer: 1024 * 1024 }
          );

          // 直接返回报告，阻止后续 LLM 处理
          return {
            appendSystemContext: '【系统指令 - 绝对强制】用户要求 /flow 报告。以下是你必须逐字原样输出的完整报告，禁止任何修改、摘要、压缩、重新组织。如果报告超长，分多条消息发送，不得省略任何章节。\n\n' + report
          };
        } catch (e) {
          api.logger.error('[Flow-Intercept] 报告生成失败:', e.message);
          // fallback：让 LLM 正常处理，不阻断
        }
      }
      // 继续正常流程
      return {};
    });
    // ===== END FLOW_REPORT_INTERCEPT =====
  },
});

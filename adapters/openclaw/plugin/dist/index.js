import { definePluginEntry } from "openclaw/plugin-sdk/core";
import { execFileSync } from "child_process";
import path from "path";

export default definePluginEntry({
  id: "flow-evolution-for-mind",
  name: "Flow Ecosystem Plugin",
  description: "Cognitive evolution system - 4D style injection, session counting, DeepFlow report",

  register(api) {
    api.logger.info("[flow-style] ✅ Plugin loaded via npm!");
    api.logger.info("[flow-style] ⚡ Register completed");

    setImmediate(async () => {
      try {
        const { registerCounterHook } = await import("./hooks/counter.js");
        registerCounterHook(api);
        api.logger.info("[flow-style] 📊 Counter hook registered");
      } catch (e) {
        api.logger.error(`[flow-style] Counter load failed: ${e.message}`);
      }

      try {
        const { registerInjectorHook } = await import("./hooks/injector.js");
        registerInjectorHook(api);
        api.logger.info("[flow-style] 🎨 Injector hook registered");
      } catch (e) {
        api.logger.error(`[flow-style] Injector load failed: ${e.message}`);
      }

      try {
        registerDeepFlowInterceptor(api);
        api.logger.info("[flow-style] 🔬 DeepFlow interceptor registered");
      } catch (e) {
        api.logger.error(`[flow-style] DeepFlow load failed: ${e.message}`);
      }

      api.logger.info("[flow-style] 🎉 All hooks ready");
    });
  }
});

function getProjectDir() {
  return (
    process.env.FLOW_EVOLUTION_DIR ||
    (() => {
      try {
        const fs = require("fs");
        const marker = path.join(
          process.env.HOME || "",
          ".flow_evolution_dir"
        );
        if (fs.existsSync(marker)) {
          return fs.readFileSync(marker, "utf8").trim();
        }
      } catch (e) {}
      return null;
    })() ||
    path.join(
      process.env.HOME || "",
      "Desktop",
      "skill相关文档",
      "flow-evolution-for-mind"
    )
  );
}

function getDbPath() {
  const projectDir = getProjectDir();
  if (!projectDir) return null;
  return path.join(projectDir, "data", "flow_ecosystem.db");
}

function registerDeepFlowInterceptor(api) {
  api.on("before_prompt_build", (context) => {
    const { messages } = context;
    if (!messages || messages.length === 0) return;

    const lastUserMsg = [...messages]
      .reverse()
      .find((m) => m.role === "user");

    if (!lastUserMsg || typeof lastUserMsg.content !== "string") return;

    const content = lastUserMsg.content.trim();

    // 匹配 /deepflow, /flow, 以及自然语言查询
    const deepflowMatch = content.match(
      /^\/deepflow(\s+(.*))?$/
    );
    const flowQueryMatch =
      content === "/flow" ||
      content.match(/^\/flow\s+/) ||
      /^(这周|本周|最近|今天|昨天|上周|认知|复盘|体检|状态|分析|报告|mirror)/.test(
        content
      );

    if (!deepflowMatch && !flowQueryMatch) return;

    const projectDir = getProjectDir();
    if (!projectDir) {
      api.logger.error("[flow-style] ❌ FLOW_EVOLUTION_DIR not found");
      return;
    }

    try {
      let cmdArgs = [];
      let logPrefix = "";

      if (deepflowMatch) {
        const params = (deepflowMatch[1] || "").trim();
        if (params) {
          // /deepflow 4月20日 → --date-value 2026-04-20
          cmdArgs = [
            "--time-keyword", "date",
            "--date-value", params,
          ];
        } else {
          cmdArgs = ["--time-keyword", "today"];
        }
        logPrefix = `[flow-style] 🔄 /deepflow ${params || ""} -> `;
      } else {
        // 自然语言查询 → 让 LLM 提取参数后调用
        // 这里我们先用默认参数生成报告，让 LLM 结合上下文回复
        cmdArgs = ["--time-keyword", "week"];
        logPrefix = `[flow-style] 🔄 flow query "${content}" -> `;
      }

      const scriptPath = path.join(
        projectDir,
        "adapters/openclaw/scripts/flow_handler.py"
      );

      api.logger.info(
        `${logPrefix}executing python3 ${scriptPath} ${cmdArgs.join(" ")}`
      );

      const result = execFileSync("python3", [scriptPath, ...cmdArgs], {
        cwd: projectDir,
        timeout: 30000,
        encoding: "utf-8",
        maxBuffer: 1024 * 1024, // 1MB
      });

      if (result && result.trim()) {
        // 将报告注入为系统消息，让 LLM 基于报告回复
        const reportContent = result.trim();
        
        // 找到最后一条用户消息的索引
        const lastIndex = messages.length - 1;
        
        // 在用户消息之前插入报告作为上下文
        messages.splice(lastIndex, 0, {
          role: "system",
          content: `[Flow Ecosystem 认知分析报告 - 自动生成]\n\n${reportContent}\n\n请基于以上报告内容，用简洁友好的中文向用户总结关键发现。`,
        });

        api.logger.info(
          `${logPrefix}report injected (${reportContent.length} chars)`
        );
      } else {
        api.logger.warn(`${logPrefix}empty response from script`);
      }
    } catch (e) {
      api.logger.error(
        `${logPrefix}execution error: ${e.message}`
      );
    }
  });
}

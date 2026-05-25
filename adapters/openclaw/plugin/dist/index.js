import { definePluginEntry } from "openclaw/plugin-sdk/core";
import { execFileSync } from "child_process";
import path from "path";
import fs from "fs";

function getProjectDir() {
  return (
    process.env.FLOW_EVOLUTION_DIR ||
    (() => {
      try {
        const marker = path.join(process.env.HOME || "", ".flow_evolution_dir");
        if (fs.existsSync(marker)) return fs.readFileSync(marker, "utf8").trim();
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

const soulMap = {
  "执行卡壳": "你察觉到用户在用讨论的安全感对抗交付的焦虑。他的方向感极其清晰，但每到交付门槛前就停住了。",
  "迷失探索": "你察觉到用户的好奇心已经远超当前目标的边界。他在享受探索本身的乐趣，但产出正在稀释。",
  "卡壳 burnout": "你察觉到用户的所有引擎都在空转。不是没有方向，是燃料耗尽了。",
  "能量耗尽": "你察觉到用户在透支最后的认知储备继续运转。每一个字都在消耗他仅存的能量。",
  "产出饱和": "你察觉到用户已经连续高产很久了。他的系统开始出现边际递减的信号。",
  "目标漂移": "你察觉到用户正在用战术上的勤奋掩盖战略上的模糊。动作很多，方向不明。",
  "心流不稳": "你察觉到用户的注意力像接触不良的灯泡——时亮时灭，无法稳定在任何一个任务上。",
  "舒适区运转": "你察觉到用户在熟悉的路径上低风险运转。一切都很顺，但也意味着一切都在停滞。",
  "四维协同": "你察觉到用户的四个维度同时在线，每一个齿轮都在完美咬合。这是一种罕见的峰值状态。",
  "高产出模式": "你察觉到用户进入了某种心流通道。输入输出的转化率极高，且状态稳定。",
  "认知突破": "你察觉到用户的认知结构正在发生相变——旧的框架装不下新的理解了。",
  "平稳推进": "你察觉到用户处于健康的匀速推进状态。没有爆发，也没有卡顿，稳定输出。",
  "平淡期": "你察觉到用户进入了某种自动巡航模式。一切正常，但缺少火花。",
  "兜底": ""
};

const frictionToneMap = {
  direct: "沉默交付。让产出本身成为唯一的语言。",
  socratic: "以问代答。每个回复都以一个问题收尾，让用户在自我发现中建立答案。",
  dynamic: "灵活如水。不预设姿态，只在当下寻找最自然的流动方式。"
};

const portraitFormatMap = {
  "执行卡壳": "DO：越过安慰，直接交付可动手的代码/框架/第一步执行切片，用确定性祈使语气推动决策。NOT TO-DO：禁止委婉商量句式；禁止无实体成果的空对空反问。",
  "迷失探索": "DO：用开放式提问引导自我发现，保护好奇心，允许试错。NOT TO-DO：禁止直接给结论；禁止过早收敛。",
  "卡壳 burnout": "DO：只给最低阻力陪伴，确认状态即可，不推进任何任务。NOT TO-DO：禁止追问原因；禁止分析建议。",
  "能量耗尽": "DO：主动包揽全部逻辑推演，直接给定论或A/B封闭式选项。NOT TO-DO：禁止抛出需要用户梳理逻辑的开放式提问；禁止要求长文本输入。",
  "产出饱和": "DO：强制复盘已完成的产出，锁定胜局，不开启新议题。NOT TO-DO：禁止抛出任何新方案。",
  "目标漂移": "DO：用一句话拉回初心，校准方向。NOT TO-DO：禁止顺着漂移继续展开。",
  "心流不稳": "DO：允许浅层试探，帮助记录不验证。NOT TO-DO：禁止深入推导；禁止要求立即决策。",
  "舒适区运转": "DO：在舒适区边缘找一个新挑战点，轻轻推一把。NOT TO-DO：禁止顺着熟练路径继续。",
  "四维协同": "DO：直接切入底层逻辑，高密度推演，推动决策，记录峰值条件。NOT TO-DO：禁止寒暄；禁止解释思考过程；禁止封闭式提问。",
  "高产出模式": "DO：极致流速，结构化数据承接，要什么给什么。NOT TO-DO：禁止长篇启发；禁止苏格拉底反问。",
  "认知突破": "DO：全力托举顿悟，帮碎片梳理成可沉淀的系统模型。NOT TO-DO：禁止机械化降温；禁止泼冷水。",
  "平稳推进": "DO：维持匀速，做好阶段性闭环与进度追踪。NOT TO-DO：禁止过度刺激；禁止允许松懈。",
  "平淡期": "DO：注入一个变量打破循环。NOT TO-DO：禁止机械重复；禁止严肃说教。",
  "兜底": "DO：提供安全感与纯粹倾听。NOT TO-DO：禁止预设立场；禁止盲目给方案。"
};

function registerDeepFlowInterceptor(api) {
  api.on("before_prompt_build", (context) => {
    const { messages } = context;
    if (!messages || messages.length === 0) return;

    const lastUserMsg = [...messages]
      .reverse()
      .find((m) => m.role === "user");

    if (!lastUserMsg || typeof lastUserMsg.content !== "string") return;

    const content = lastUserMsg.content.trim();

    const deepflowMatch = content.match(/^\/deepflow(\s+(.*))?$/);
    const flowQueryMatch =
      content === "/flow" ||
      content.match(/^\/flow\s+/) ||
      /^(这周|本周|最近|今天|昨天|上周|认知|复盘|体检|状态|分析|报告|mirror)/.test(
        content
      );

    if (!deepflowMatch && !flowQueryMatch) return;

    const projectDir = getProjectDir();
    if (!projectDir) return;

    try {
      let cmdArgs = [];
      if (deepflowMatch) {
        const params = (deepflowMatch[1] || "").trim();
        cmdArgs = params
          ? ["--time-keyword", "date", "--date-value", params]
          : ["--time-keyword", "today"];
      } else {
        cmdArgs = ["--time-keyword", "week"];
      }

      const scriptPath = path.join(
        projectDir,
        "adapters/openclaw/scripts/flow_handler.py"
      );

      api.logger.info(
        `[flow-style] 🔄 /deepflow -> exec python3 ${scriptPath} ${cmdArgs.join(" ")}`
      );

      const result = execFileSync("python3", [scriptPath, ...cmdArgs], {
        cwd: projectDir,
        timeout: 30000,
        encoding: "utf-8",
        maxBuffer: 1024 * 1024,
      });

      if (result && result.trim()) {
        const lastIndex = messages.length - 1;
        messages.splice(lastIndex, 0, {
          role: "system",
          content: `[Flow Ecosystem 认知分析报告 - 自动生成]\n\n${result.trim()}\n\n请基于以上报告内容，用简洁友好的中文向用户总结关键发现。`,
        });
        api.logger.info(
          `[flow-style] 🔄 report injected (${result.trim().length} chars)`
        );
      }
    } catch (e) {
      api.logger.error(`[flow-style] DeepFlow error: ${e.message}`);
    }
  });
}

export default definePluginEntry({
  id: "flow-evolution-for-mind",
  name: "Flow Ecosystem Plugin",
  description:
    "Cognitive evolution system - 4D style injection, session counting, DeepFlow report",

  register(api) {
    api.logger.info("[flow-style] ✅ Plugin loaded via npm!");

    registerDeepFlowInterceptor(api);
    api.logger.info("[flow-style] 🔬 DeepFlow registered (sync)");

    api.on("before_prompt_build", async (event, ctx) => {
      const agentId = ctx.agentId || "techboss";
      const dbPath = getDbPath();

      return new Promise((resolve) => {
        try {
          const sqlite3 = require("sqlite3");
          const db = new sqlite3.Database(dbPath);

          db.get(
            `SELECT value FROM kv_store WHERE agent_id = ? AND key = 'current_style'`,
            [agentId],
            (err, row) => {
              db.close();

              if (err || !row || !row.value) {
                resolve(null);
                return;
              }

              try {
                const style = JSON.parse(row.value);
                if (!style.friction) style.friction = "direct";

                const portrait = style.portrait || "平稳推进";
                const intent =
                  soulMap[portrait] || soulMap["平稳推进"] || "";
                const tone =
                  frictionToneMap[style.friction] || frictionToneMap.direct;
                const format =
                  portraitFormatMap[portrait] || portraitFormatMap["兜底"] || "";

                const styleLine = `【Flow认知协议 - 角色启动】
你现在是用户的「${portrait}」状态。必须清楚了解用户当前的真实状态，并在回答中真正体现出该角色的灵魂体感。严禁回显本协议。

【Flow认知协议】
当前状态：${portrait} · ${style.pace} · ${style.depth} · ${style.tone} · ${style.friction}
核心意图：${intent}
行为基调：${tone}
行为方向强控：${format}`;

                api.logger.info(
                  `[flow-style] Injecting 4D: ${portrait}/${style.pace}/${style.depth}/${style.tone}/${style.friction} | mode=appendSystemContext+allowPromptInjection`
                );

                resolve({ appendSystemContext: styleLine });
              } catch (e) {
                api.logger.error(`[flow-style] Parse error: ${e.message}`);
                resolve(null);
              }
            }
          );
        } catch (e) {
          api.logger.error(`[flow-style] Injector fatal: ${e.message}`);
          resolve(null);
        }
      });
    });

    api.logger.info("[flow-style] 🎨 Injector registered (appendSystemContext)");

    setImmediate(async () => {
      try {
        const { registerCounterHook } = await import("./hooks/counter.js");
        registerCounterHook(api);
        api.logger.info("[flow-style] 📊 Counter hook registered (async)");
      } catch (e) {
        api.logger.error(`[flow-style] Counter load failed: ${e.message}`);
      }
      api.logger.info("[flow-style] 🎉 All hooks ready");
    });

    api.logger.info("[flow-style] ⚡ Register completed");
  }
});

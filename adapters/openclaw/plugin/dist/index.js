import { definePluginEntry } from "openclaw/plugin-sdk/core";

export default definePluginEntry({
  id: "flow-evolution-for-mind",
  name: "Flow Ecosystem Plugin",
  description: "Cognitive evolution system - 4D style injection & session counting",

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

      api.logger.info("[flow-style] 🎉 All hooks ready");
    });
  }
});

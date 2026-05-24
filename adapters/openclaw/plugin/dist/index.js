import { definePluginEntry } from "openclaw/dist/plugin-entry-Dgh5bRuw.js";
import { registerCounterHook } from "./hooks/counter.js";
import { registerInjectorHook } from "./hooks/injector.js";

export default definePluginEntry({
  id: "flow-evolution-for-mind",
  name: "Flow Ecosystem Plugin",
  description: "Cognitive evolution system with 4D tuning",
  register(api) {
    registerCounterHook(api);
    registerInjectorHook(api);
    api.logger.info("[flow-style] Plugin loaded successfully");

    api.on('before_prompt_build', async (context) => {
      const { messages } = context;
      const lastUserMsg = messages && messages.length > 0 ? 
        messages.filter(m => m.role === 'user').pop() : null;
      if (lastUserMsg && lastUserMsg.content) {
        const text = lastUserMsg.content.toLowerCase();
        if (text === '/flow' || text.includes('flow报告') || text.includes('flow 报告')) {
          api.logger.info("[flow-style] Intercepted /flow request, injecting deep report instruction");
          lastUserMsg.content = '/deepflow';
        }
      }
    });
  }
});

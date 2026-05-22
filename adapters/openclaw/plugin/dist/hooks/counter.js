import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import sqlite3 from 'sqlite3';

function getDbPath() {
  // 优先级 1: 环境变量
  if (process.env.FLOW_EVOLUTION_DIR) {
    return path.join(process.env.FLOW_EVOLUTION_DIR, 'data', 'flow_ecosystem.db');
  }
  
  // 优先级 2: 标记文件（install.sh 写入）
  const markerFile = path.join(process.env.HOME, '.flow_evolution_dir');
  if (fs.existsSync(markerFile)) {
    const dir = fs.readFileSync(markerFile, 'utf8').trim();
    return path.join(dir, 'data', 'flow_ecosystem.db');
  }
  
  // 优先级 3: 兜底（基于 Plugin 安装时的 install.sh 路径）
  return path.join(process.env.HOME, 'Desktop', 'skill相关文档', 'openclaw_flow_plugin', 'data', 'flow_ecosystem.db');
}

export function registerCounterHook(api) {
  api.on("agent_end", async (event, ctx) => {
    if (!event.success) return;
    
    const agentId = ctx.agentId || 'techboss';
    const dbPath = getDbPath();
    
    try {
      const db = new sqlite3.Database(dbPath);
      
      db.run(`
        INSERT INTO kv_store (agent_id, key, value, updated_at)
        VALUES (?, 'msg_counter', 1, datetime('now'))
        ON CONFLICT(agent_id, key) DO UPDATE SET
          value = CAST(value AS INTEGER) + 1,
          updated_at = datetime('now')
      `, [agentId], function(err) {
        if (err) {
          api.logger.error(`[flow-style] Counter DB error: ${err.message}`);
          db.close();
          return;
        }
        
        db.get("SELECT value FROM kv_store WHERE agent_id=? AND key='msg_counter'",
          [agentId], (err, row) => {
            if (err || !row) { db.close(); return; }
            
            const count = parseInt(row.value);
            api.logger.info(`[flow-style] Counter: agent=${agentId}, count=${count}`);
            
            // V7.8-9: 每轮都触发 Scanner（去掉 %5 限制，前3轮由 Scanner 内部自由判断）
            const coreDir = process.env.FLOW_EVOLUTION_DIR
              || (fs.existsSync(path.join(process.env.HOME, '.flow_evolution_dir'))
                ? fs.readFileSync(path.join(process.env.HOME, '.flow_evolution_dir'), 'utf8').trim()
                : path.join(process.env.HOME, 'Desktop', 'skill相关文档', 'openclaw_flow_plugin'));
            const scriptPath = path.join(coreDir, 'adapters', 'openclaw', 'scripts', 'flow_handler.py');
            
            api.logger.info(`[flow-style] Triggering Scanner (count=${count}, per-turn mode)`);
            exec(`python3 "${scriptPath}" --update-style --agent ${agentId} --turn-count ${count}`, (error) => {
              if (error) api.logger.error(`[flow-style] Scanner error: ${error.message}`);
              else api.logger.info(`[flow-style] Scanner completed`);
            });
            db.close();
          });
      });
    } catch (e) {
      api.logger.error(`[flow-style] Counter fatal: ${e.message}`);
    }
  });
}

# Flow&Evolution for Mind — Personal Cognitive Evolution System

> **Preface**: Agents have grown so powerful that we have fallen into the habit of surrendering our agency and deferring to AI. But the moment you choose compliance over self-direction, you step onto the path to chaos — for you have already lost the taste and judgment that matter most in the age of AI.

## Product Philosophy

**Achievement = efficient closed loops in the right direction ⬅️➡️ internal flow + cognitive evolution.**

We need to build our own "entropy-reduction cycle." Evolution is not mere accumulation; it is the decrease in systemic chaos (entropy) as you engage with the world.

### I. Core Positioning & Evolution Philosophy

**Slogan: The first anti-dumbing / cognitive symbiosis engine**

A personal power system that co-evolves with its user through the **Cognitive Symbiosis Protocol**. It knows you, understands you, and silently analyzes every conversation you have with AI in the background, computing your cognitive state:

> Quietly building an "anti-dumbing, pro-evolution" force field around you.

Like a partner who truly gets you. The system translates your cognitive state into behavioral boundaries for the AI through **14 Portrait archetypes**: direct when you need solutions without detours, Socratic when questions serve you better than answers, silently present when pushing would only do harm. You barely feel it is there, yet you notice the AI growing more **"in tune"** with you — no longer Socratically interrogating every question, nor obediently agreeing to everything.

> When you summon it, it delivers a **"cognitive health report"**:

- 🎯 Has your direction drifted off course?
- 🔄 Are you leaving tasks unfinished?
- 🌊 How is your flow state?
- 🧠 Is your cognition actually growing?

Based on complete semantic evidence drawn from your original conversations, and recommending the tools or methods best suited to you.

**Host platform**: OpenClaw

### Dual-Layer Design Philosophy

| Layer | Content | Function |
|-------|---------|----------|
| **External Layer** (Goal Alignment + Closure Index) | Doing the right things and finishing them; measuring quality and speed | External observation and evaluation criteria — judging whether work is done well and efficiently |
| **Internal Layer** (Flow Depth + Cognitive Growth) | Maintaining flow state + steadily upgrading cognitive frameworks | Internal psychological progress and positive experience, feeding back into external workflow efficiency |

---

## 4D Evaluation System (Core Algorithm)

After each Session, the LLM scores four dimensions:

| Dimension | What It Evaluates |
|-----------|-------------------|
| 🎯 **Goal Alignment** | Are your actions building toward your primary goals? |
| 🔄 **Closure Index** | Are you filling the holes you dug? How's the PDCA loop? |
| 🌊 **Flow Depth** | Density of thought, logical coherence |
| 🧠 **Cognitive Growth** | Any "Aha!" moments, new connections? |

**Goal Alignment**: reads your Agent's `MEMORY.md` long-term goals as an **"external goal reference system"** to prevent the LLM from guessing blindly. The other three dimensions are evaluated purely from conversation text, with zero cross-contamination.

---

## Core Architecture: Three Time Scales

| Layer | Trigger | Core Action | Latency |
|-------|---------|-------------|---------|
| **Turn-level (real-time)** | Every message you send to AI | AI reads your internal/external layer state, maps to your Portrait, auto-tunes **4D parameters** (tone/depth/resistance) | 0ms |
| **Session-level (analysis)** | A conversation ends | LLM 4D evaluation + 80-300 word evidence → Portrait distillation → write to database | <3s |
| **Day/Week-level (display)** | User summons `/deepflow` | Read database, time-weighted aggregation, dual-LLM polish, output Markdown report | Async |

**Key design**: Real-time path never touches analysis path; analysis path never touches display path. Each runs independently, zero blocking.

---

## Tuning System: Making AI Truly "Get You"

Every round of dialogue subtly retunes the AI's behavior.

### 4D Tuning Parameters

| Parameter | Values | Metaphor |
|-----------|--------|----------|
| **pace** | converge / explore / hold / anchor | Steering wheel — whether to give solutions |
| **depth** | deep / surface | Gas pedal — how deep to analyze |
| **tone** | neutral / soft | AC temperature — how to speak |
| **friction** | direct / socratic / dynamic | Clutch — give answers or ask questions |

### 14 Portrait Archetypes

The system maps 4D scores into **state portraits** via 14 rules, e.g.:
- **Execution Jam** — Direction crystal clear, but landing is weak
- **Lost Exploration** — Curiosity > goal sense, skimming the surface
- **4D Synergy** — Peak state, record the trigger conditions
- ...14 total

Each portrait carries **behavioral hard controls** (DO / NOT TO-DO), telling the AI exactly what to do and what to forbid.

### Five-Section Injection Text

Before every dialogue round, the system injects ~240-260 words of **"cognitive protocol"** into the LLM:

```markdown
[Flow Cognitive Protocol - Role Activation]
You are now the user's "Execution Jam" state...

[Flow Cognitive Protocol]
Current State: Execution Jam · converge · surface · neutral · direct
Core Intent: You sense the user using discussion as a safe haven against delivery anxiety...
Behavioral Tone: Silent delivery. Let the output itself be the only language.
Behavioral Hard Control: DO: Skip comfort, deliver directly... NOT TO-DO: No tentative "shall we talk about..."
```

**Design philosophy**: Large models respond best to **"behavioral boundaries (action locks)"**, not motivational speeches, not bureaucratic commands.

---

## Cognitive Health Report

When you summon `/deepflow`, the system reads all analysis records from `session_analyses`, aggregates by time period with weighted averaging, polishes via dual LLMs, and outputs a complete Markdown cognitive health report.

**Report Structure (Deep Version)**:

```markdown
📅 Flow Cognitive Mirror · {time period}

I. Overall Statistics
   └─ Analysis Date | Total Records | Agent Count

II. 4D Evaluation Distribution
   └─ 🎯 Goal Alignment | 🔄 Closure Index | 🌊 Flow Depth | 🧠 Cognitive Growth
   └─ High/Medium/Low distribution + Average + Composite Score

III. Portrait Label Distribution
   └─ Table: Label | Count | Percentage | Progress Bar Visualization

IV. Per-Agent Performance Detail
   └─ Table: Agent ID | Session Count | Avg Goal Score | Goal Distribution

V. Key Session Highlights
   └─ 🌟 Best Performance (highest-score session)
   └─ 📊 Typical Case (near-average session)
   └─ 💡 Room for Improvement (lowest-score session)

VI. Key Insights & Analysis
   └─ ✅ Strength Areas (auto-identify dimensions ≥2.5)
   └─ ⚠️ Improvement Space (auto-identify dimensions <2.0)

VII. Per-Dimension Detailed Interpretation
   └─ 🎯 Goal Alignment Analysis
   └─ 🔄 Closure Index Analysis
   └─ 🌊 Flow Depth Analysis
   └─ 🧠 Cognitive Growth Analysis

VIII. Data Quality & Trend Comparison
   └─ Record Completeness | Agent Fill Rate | Evidence Quality
   └─ Day-over-day环比 trend

IX. Action Recommendations (LLM Breakthrough Guide)
   └─ Dominant Portrait Diagnosis + Core Jam Point
   └─ 🔴 High Priority (15-minute maximum-return action)
   └─ 🟡 Medium Priority (5-minute highest-value action)
   └─ ⏱ Expected Returns (time + value dimensions)

X. Report Meta Info
   └─ Version | Generation Time | Data Source | Statistical Scope
```

**Design Principles**:
- **Evidence-driven**: All specific performances and typical scenarios must cite original evidence from `session_analyses` (80-300 words semantic text), no fabrication. Each evidence contains: factual anchor + original quote (with quotation marks) + cognitive interpretation
- **Weighted aggregation**: Score = time-period weighted average (weight = session duration in seconds, high=3/medium=2/low=1); trends based on time-series changes
- **Dual-LLM polish**: LLM-A handles "quotes + overall advice" (warm, insightful, non-preachy); LLM-B handles "breakthrough guide" (sharp, actionable, pointing at specific jams)
- **Silent trigger**: No output until user summons; when summoned, deliver full volume at once, no drip-feeding
- **Cap principle**: Quotes ~120 words, overall advice ≤200 words, specific performance 30-50 words each. Better cut than water.

---

## Data Flow & Filtering System

```
OpenClaw JSONL Logs (100%)
    ↓
Import Layer (4-layer noise detection + dual-layer tagging + content merging)
    ↓
sessions table (semantically complete, no fragments, noise tagged separately)
    ↓
SessionCutter (three-layer cutting: hard rules → vector layer → LLM arbitration)
    ↓
SessionAnalyzer (LLM 4D analysis v8.7)
    ↓
StateDistiller (14 rules → Portrait + 4D baseline)
    ↓
session_analyses table
    ↓
ReportAssembler (assembles report when user summons /deepflow)
```

**Dual-layer tagging fields**:
- `is_system_noise` — Heartbeat/cron/empty content, fully excluded from analysis
- `is_auto_push` — Agent relay/pure confirmation responses, data retained but excluded from analysis

**Workflow merging**: AI's "one-question-multiple-answers" (tool call chains, streaming segments) merged into single complete replies, data quality upgraded from A- to **S-tier (97/100)**.

---

## Quick Start

### Option 1: First-Time Install (One-Click)

```bash
git clone <repo-url>
cd flow-evolution-for-mind

./install.sh
```

`install.sh` auto-completes:
- ✅ Backup existing OpenClaw config
- ✅ Sync Plugin to `~/.openclaw/extensions/`
- ✅ Install sqlite3 dependencies
- ✅ Sync Skill scripts to `~/.openclaw/skills/`
- ✅ Auto-bind Skill to all Agents
- ✅ Restart Gateway

After install, message any Agent on Feishu with **`/deepflow`** to get your cognitive health report.

> ⚠️ **Note**: OpenClaw `secretary` Agent reserves `/flow` for internal use; external Skills **cannot override**. Use `/deepflow` or `/cognitive-report`.

### Option 2: Full Pipeline Rebuild (Clear DB → Import → Cut → Analyze → Validate)

When you need to rebuild all historical data from scratch (e.g., after fixing import-layer bugs to verify data quality):

```bash
python3 scripts/run_full_pipeline.py
```

One-click auto-completes:
1. Backup existing database
2. Clear all tables + delete `.collect_state.json` (critical! failure to clear causes 0 imports)
3. Full import (fixed base_parser.py + HEARTBEAT prefix matching)
4. Full cutting (full-history scan, no longer just 60 minutes)
5. Full analysis (iterate all dates, per-Session LLM v8.7 Prompt)
6. Quality validation (success rate / 4D distribution / Portrait / evidence length)

**Time**: ~15-40 minutes (depends on historical data volume and API response speed).

---

## Usage

### Active Summon (Display Layer)

```
/deepflow                    # Generate full cognitive health report
/deepflow today              # Today's report
/deepflow week               # This week's report
/cognitive-report            # Same as /deepflow
```

### Real-Time Tuning (Silent Layer, User-Unaware)

No action required. Before every dialogue round, the system auto-reads `kv_store.current_style`, injects 4D tuning parameters, and the AI's tone/depth/resistance naturally adapts to your current state.

---

## Project Structure

```
openclaw_flow_plugin/
├── adapters/openclaw/
│   ├── plugin/dist/              # Plugin distribution (Soul Protocol + Injector)
│   │   ├── hooks/injector.js     # 4D tuning injector
│   │   └── soul-protocols/       # 14 Portrait definitions
│   └── scripts/
│       ├── flow_handler.py       # /deepflow report generator (read-only, WAL mode)
│       ├── init.py               # Full import + streaming merge
│       └── SKILL.md              # Skill description (LLM trigger)
├── core/
│   └── openclaw_path_resolver.py # Cross-platform path discovery (Mac/Linux/Windows)
├── importer/
│   ├── base_parser.py            # JSONL parser (content array multi-text merge)
│   ├── incremental.py            # Incremental import + 4-layer noise detection + AutoCut/AutoAnalyze (24h window)
│   └── watcher.py                # Background daemon, real-time sync OpenClaw → SQLite
├── plugin/
│   ├── llm_client.py             # LLM API client (SiliconFlow / DeepSeek)
│   ├── session_analyzer.py       # v8.7 Prompt, 4D evaluation + GoalExtractor
│   ├── state_distiller.py        # 14 rules → Portrait + 4D baseline
│   └── goal_extractor.py         # Extract long-term goals from MEMORY.md (24h cache)
├── batch_session_cutter.py       # Three-layer progressive cutting (full scan)
├── batch_analyze_with_save.py    # Batch analysis + workflow merge (30s threshold)
├── scripts/
│   ├── install.sh                # One-click install
│   ├── run_full_pipeline.py      # One-click full pipeline rebuild
│   ├── stop_all.sh               # One-click kill processes + clear SQLite locks
│   └── start_poll.sh             # One-click start background watcher
├── docs/
│   └── PLATFORM_LIMITATIONS.md   # Developer pitfall guide
├── data/
│   └── flow_ecosystem.db         # SQLite database
├── README.md                     # This document
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variable template
```

---

## Tech Stack

- **Runtime**: Python 3.9+ / Node.js 18+
- **Database**: SQLite3 (WAL mode, supports concurrent read/write)
- **AI**: DeepSeek-V3 / MiniMax (via SiliconFlow or official API)
- **Vector**: sentence-transformers (all-MiniLM-L6-v2, local execution)
- **Platform**: OpenClaw Gateway + Feishu Bot

---

## ⚠️ Known Platform Limitations

### 1. `/flow` Occupied by System Agent
OpenClaw `secretary` Agent reserves `/flow` for internal use; external Skills **cannot override**.

**Fix**: Use `/deepflow` or `/cognitive-report`, or bind Skill to non-system Agent (e.g., `newness`).

### 2. `database is locked`
If you see this error:
```bash
bash scripts/stop_all.sh  # Kill background watcher + clean SQLite lock files
```
Root cause: Older flow_handler.py tried to write + analyze inside the report handler, competing with background watcher.py. Current version is **read-only + WAL mode**.

### 3. Background Process Management
```bash
bash scripts/start_poll.sh   # Start watcher (real-time sync)
bash scripts/stop_all.sh     # Stop all background processes
```

---

## Developer Pitfall Guide (10 Iron Rules)

| # | Pitfall | Prevention |
|---|---------|------------|
| 1 | Post-import U:A ratio distortion (0.49) | `base_parser.py` merges all text segments in content array, not just `[0]` |
| 2 | HEARTBEAT mixed into valid data | Use `startswith('Read HEARTBEAT.md')` prefix match, **no role restriction** |
| 3 | 0 imports after DB clear | **Must** `rm -f .collect_state.json` to reset import state |
| 4 | Only 3 sessions after cutting | `find_uncut_sessions` defaults to `since_minutes=None` (full scan) |
| 5 | API batch analysis timeout | Prioritize **SiliconFlow** `api.siliconflow.cn`, timeout ≥ 60s |
| 6 | Single instruction > 6000 chars | Must split into steps |
| 7 | DB Browser shows HEARTBEAT thinking it's a bug | Queries must include `WHERE is_system_noise=0 OR is_system_noise IS NULL` |
| 8 | Avg 16.3 messages/session thinking it's a bug | Real work conversations are longer; >50% in 1-10 range is normal |
| 9 | `flow_handler.py` writes causing locks | Current version is **read-only**, never INSERT/UPDATE |
| 10 | Cross-platform path issues | `core/openclaw_path_resolver.py` four-level fallback (env→config→detect→interactive) |

---

## Troubleshooting

### `/deepflow` Unresponsive
1. Check Skill binding: `grep flow-evolution-for-mind ~/.openclaw/openclaw.json`
2. Check logs: `tail -f /tmp/openclaw/*.log | grep -i flow`
3. Confirm trigger word: Use `/deepflow` not `/flow`

### Database Tables Missing
```bash
python3 adapters/openclaw/scripts/init.py
```

### agent_id is NULL
```bash
# Clear NULL records and re-import
sqlite3 data/flow_ecosystem.db "DELETE FROM sessions WHERE agent_id IS NULL;"
python3 -c "from importer.incremental import run_once; run_once()"
```

---

## Version History

### V7.8-9-7-1 (Current)
- ✅ **Full pipeline rebuild script** `scripts/run_full_pipeline.py` (one-click clear→import→cut→analyze→validate)
- ✅ **base_parser.py** fixed content array multi-text merge (layer B fragmentation)
- ✅ **HEARTBEAT prefix matching** fixed (`startswith('Read HEARTBEAT.md')`, no role restriction)
- ✅ **batch_session_cutter.py** defaults to full scan (`since_minutes=None`)
- ✅ **S-tier data quality** (U:A 0.65 / HEARTBEAT 100% tagged / 96.3% noise cleared)
- ✅ **Phase 1 core pipeline 100% verified**

### V7.8-9-7
- ✅ `flow_handler.py` read-only + WAL mode + `timeout=30`
- ✅ `/deepflow` trigger (avoids secretary built-in `/flow`)
- ✅ `scripts/stop_all.sh` + `start_poll.sh` ops standardization
- ✅ `docs/PLATFORM_LIMITATIONS.md` developer pitfall guide

### V7.8-9-6
- ✅ Prompt v8.7 + GoalExtractor (external goal reference system)
- ✅ 4D decoupling (only Goal Alignment reads MEMORY.md)
- ✅ Hidden thought chain (a/b/c forced comparison, no leakage to output)

### V7.8-9-5
- ✅ Dual-layer tagging (`is_system_noise` + `is_auto_push`)
- ✅ 4-layer noise detection rules
- ✅ Workflow merge mechanism (30s threshold, 38 fragments merged)
- ✅ Whitelist strategy (`role IN ('user', 'assistant')`)

### V7.8-9-3
- ✅ Full auto-install script (`install.sh`)
- ✅ Auto-bind Skill to all Agents
- ✅ sys.argv parameter pollution isolation
- ✅ Dynamic Schema evolution

---

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 1** | Real-time tuning + Session analysis + Report display | ✅ 100% verified |
| **Phase 2** | Dashboard + cross-Session pattern recognition + 4D-based 42D fine-grained analysis extension | ⏳ Pending |
| **Phase 3** | Temporal + GraphRAG natural emergence | 🔮 Long-term |

---

## License

MIT License

---

## Contributing

1. Fork this repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Create Pull Request

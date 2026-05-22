from typing import List, Dict, Optional
import time
import re
from plugin.state_distiller import StateDistiller
from plugin.session_splitter import split_messages_by_time, generate_sub_session_id

class SessionAnalysis:
    def __init__(self, goal_alignment='', closure_index='', flow_depth='', cognition_growth='',
                 goal_evidence='', closure_evidence='', flow_evidence='', cognition_evidence='', session_id=None,
                 portrait_label=None, portrait_description=None, portrait_suggestion=None, portrait_rule_insight=None,
                 style_pace=None, style_depth=None, style_tone=None, style_friction=None):
        self.goal_alignment = goal_alignment
        self.closure_index = closure_index
        self.flow_depth = flow_depth
        self.cognition_growth = cognition_growth
        self.goal_evidence = goal_evidence
        self.closure_evidence = closure_evidence
        self.flow_evidence = flow_evidence
        self.cognition_evidence = cognition_evidence
        self.session_id = session_id
        # Portrait & Style (from StateDistiller)
        self.portrait_label = portrait_label
        self.portrait_description = portrait_description
        self.portrait_suggestion = portrait_suggestion
        self.portrait_rule_insight = portrait_rule_insight
        self.style_pace = style_pace
        self.style_depth = style_depth
        self.style_tone = style_tone
        self.style_friction = style_friction

class SessionAnalyzer:
    PROMPT_TEMPLATE = '''# Role: 认知分析师 (Cognitive Analyst)

## 任务说明
请阅读下方的【对话原文】，严格基于【4D认知扫描矩阵】和【外部目标参照】，对用户在当前 Session 中的表现进行立体诊断。

## 输出要求
严格按以下格式输出 4 行纯文本，禁止输出 JSON，禁止输出 Markdown 标题，禁止对前缀（如"目标对齐度："）加 ** 粗体：

目标对齐度：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
闭环指数：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
心流深度：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]
认知成长：[高/中/低]，证据：[80-300字，State Change单段式，宁少勿水]

---

## ⚖️ 证据生成硬约束（违反将导致输出失败）

1. 【核心内容】只记录导致用户状态变更（State Change）的行为。如：用户推翻旧想法、提出新框架/定义、拒绝建议、展现强烈情绪/判断、主动做优先级调整、话题漂移。
2. 【语调视角的"四不准"】
   - 必须像老朋友在帮用户复盘，绝不要冷冰冰的"审计报告"感。
   - 禁止系统视角：绝对不要描述"助手响应了什么"、"系统做了什么"。
   - 禁止流水账：绝对禁止按时间顺序罗列事件（"接着...然后...随后...最后..."）。
   - 禁止纯形容词堆砌（如"很好"、"顺利"、"明确"），原话必须真实存在。
3. 【证据字数控制】
   - 证据物理字数要求：80 字下限保证事实，150 字舒适区，300 字硬上限。
   - 宁少勿水，1句话把关键变动说清楚就立刻停，禁止硬凑字数，但必须完整结尾。

---

## 🎯 外部目标参照（仅用于评估"目标对齐度"，其他维度严禁引用）
{goals_text}

---

## 🧠 4D 认知扫描矩阵

### 1. 目标对齐度 (Navigation)
* 【隐藏思考链】评估前必须在内心先回答以下 3 个问题（不输出思考过程）：
  a. 本对话核心主题与【外部目标参照】中的哪个目标或技术实体（如Graphiti/Mem0等）相关？
  b. 若相关，是否明显推进了里程碑（高=推进，中=维持，低=停滞）？若无关，属于健康探索还是用简单任务逃避主线（目标漂移）？
* 【核心扫描点】方向稳定性 / 优先级清晰度 / 纠偏主动性 / 目标具象化（从想做什么转为怎么做）
* 【特别约束】若判定为[高/中]，证据中必须与对应的外部目标关键词或技术实体有直接或间接的关系；若判定为[低]，必须指出用户在死磕什么从而偏离了主线。

### 2. 闭环指数 (Closure)
* 【核心扫描点（PDCA）】
  - 计划明确性(P)：有无定义下一步的首步动作。
  - 执行推进度(D)：有无做出实际决策或代码操作。
  - 验证完整性(C)：有无结论产出。
  - 调整闭环度(A)：有无基于反馈进行迭代修正。

### 3. 心流深度 (Flow)
* 【核心扫描点】逻辑链深度（推理层级）/ 有序度（讨论层层递进）/ 追问持续性（刨根问底）/ 专注信号（连续深入无打断）/ 元认知（反思自己的方法论）。
* 【补充规则】若在此维度无明显的"状态突变"，证据应全力捕捉"高密度、长时间持续专注推进"的行为事实。

### 4. 认知成长 (Cognition)
* 【核心扫描点】逻辑链条长度 / 概念密度（新框架、新概念涌现）/ 自我修正（果断推翻旧判断）/ 跨域连接（方法论迁移）/ 方法论提炼（抽象出通用底层规则）。

---

## 【对话原文】
{dialog_text}
'''

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def analyze_batch(self, messages: List[Dict], session_id: str = None, gap_minutes: int = 15, agent_id: str = None) -> List[SessionAnalysis]:
        """按15分钟切割后批量分析，返回多个 SessionAnalysis"""
        chunks = split_messages_by_time(messages, gap_minutes)
        if not chunks:
            return []

        results = []
        for idx, chunk in enumerate(chunks, 1):
            sub_id = generate_sub_session_id(session_id, idx) if session_id else None
            result = self._analyze_single(chunk, sub_id, agent_id=agent_id)
            if result:
                results.append(result)

        return results

    def analyze(self, messages: List[Dict], session_id: str = None, agent_id: str = None) -> Optional[SessionAnalysis]:
        """兼容旧接口：按15分钟切割后分析，返回第一个子 session 结果"""
        results = self.analyze_batch(messages, session_id, gap_minutes=15)
        return results[0] if results else None

    def _analyze_single(self, messages: List[Dict], session_id: str = None, agent_id: str = None) -> Optional[SessionAnalysis]:
        """分析单个子 session（原 analyze 核心逻辑）"""
        dialog_text = self._format_messages(messages)
        goals_text = self._get_goals_text(agent_id) if agent_id else "未声明目标"
        prompt = self.PROMPT_TEMPLATE.format(dialog_text=dialog_text, goals_text=goals_text)
        start = time.time()
        response = self.llm_client.chat(prompt)
        latency = int((time.time() - start) * 1000)
        result = self._parse_response(response)
        if result and session_id:
            result.session_id = session_id
        
        # === 新增：StateDistiller 画像蒸馏 ===
        if result:
            try:
                distiller = StateDistiller()
                portrait = distiller.distill(
                    result.goal_alignment,
                    result.closure_index,
                    result.flow_depth,
                    result.cognition_growth
                )
                if portrait:
                    result.portrait_label = portrait.label
                    result.portrait_description = portrait.description
                    result.portrait_suggestion = portrait.suggestion
                    result.portrait_rule_insight = portrait.rule_insight
                    result.style_pace = portrait.style_pace
                    result.style_depth = portrait.style_depth
                    result.style_tone = portrait.style_tone
                else:
                    raise ValueError("StateDistiller 返回 None")
            except Exception as e:
                print(f"⚠️ StateDistiller 失败，使用默认值: {e}")
                result.portrait_label = '平稳推进'
                result.portrait_description = '状态平稳，保持观察'
                result.portrait_suggestion = '保持当前节奏'
                result.portrait_rule_insight = '状态组合未命中明确规则，保持观察'
                result.style_pace = 'explore'
                result.style_depth = 'deep'
                result.style_tone = 'neutral'
        # === 新增结束 ===
        
        if result:
            for dim_name, ev in [
                ('目标对齐', result.goal_evidence),
                ('闭环指数', result.closure_evidence),
                ('心流深度', result.flow_evidence),
                ('认知成长', result.cognition_evidence)
            ]:
                if not ev or len(ev.strip()) < 20:
                    raise ValueError(f"{dim_name}证据过短({len(ev) if ev else 0}字)，拒绝写入")
        
        return result

    def _format_messages(self, messages: List[Dict]) -> str:
        """过滤空内容 + 合并连续 assistant + 代码块/引用块指纹化压缩"""
        from plugin.session.preprocessor import TurnPreprocessor

        preprocessor = TurnPreprocessor()

        # 1. 过滤：只保留有有效 content_text 的 user/assistant
        valid_msgs = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content_text', '') or ''
            if role in ('user', 'assistant') and len(content.strip()) > 5:
                valid_msgs.append(msg)

        # 2. 合并连续 assistant 消息（同一轮回复被切分的情况）
        merged = []
        for msg in valid_msgs:
            role = msg.get('role', '')
            content = str(msg.get('content_text', '') or '').strip()
            if role == 'assistant' and merged and merged[-1]['role'] == 'assistant':
                merged[-1]['content_text'] += '\n\n' + content
            else:
                merged.append({'role': role, 'content_text': content})

        # 3. 指纹化压缩：复用 TurnPreprocessor（原 VectorLayer 设计，现 Analyzer 共享）
        # VectorLayer 用 embedding_text（限1000字，含hash），Analyzer 用 user_notes + 块标记（无hash）
        dialog_text = ""
        for msg in merged:
            role = msg['role']
            content = msg['content_text']

            # 提取各类块
            code_blocks = preprocessor._extract_code_blocks(content)
            quote_blocks = preprocessor._extract_quote_blocks(content)
            list_blocks = preprocessor._extract_long_lists(content)

            # 提取用户原创注释（去掉所有块后的纯用户思考）
            user_notes = preprocessor._extract_user_notes(content, code_blocks, quote_blocks, list_blocks)

            # 拼接：用户注释 + [类型:行数] 摘要（去掉无意义的 hash，保留语义锚点）
            parts = []
            if user_notes:
                parts.append(user_notes)
            for block in code_blocks:
                lines = block['snippet'].count('\n') + 1
                parts.append(f"[代码块:{lines}行] {block['snippet']}")
            for block in quote_blocks:
                parts.append(f"[引用块] {block['snippet']}")
            for block in list_blocks:
                parts.append(f"[列表块] {block['snippet']}")

            cleaned_content = ' '.join(parts)
            dialog_text += f"{role}: {cleaned_content}\n"

        # 不截断：保留全部消息，观察 LLM 实际表现（V7.8-1 实验策略）
        return dialog_text

    def _parse_response(self, response: str) -> Optional[SessionAnalysis]:
        if not response:
            return None
        
        # Markdown 清洗：去掉粗体、标题、分隔线等格式干扰
        response = response.replace('**', '').replace('__', '').replace('---', '')
        response = response.replace('### ', '').replace('## ', '').replace('# ', '')
        response = re.sub(r'<[^>]+>', '', response)
        
        pattern = r'(目标对齐度|闭环指数|心流深度|认知成长)[:：]\s*\[?\s*([高中低])\s*\]?\s*[，,、:：]\s*证据[:：]\s*(.+?)(?=\n\s*(目标对齐度|闭环指数|心流深度|认知成长)|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        if len(matches) != 4:
            print(f"[解析警告] 只匹配到 {len(matches)} 个维度，原始响应：{response[:300]}")
            return None
        dim_map = {m[0]: (m[1], m[2].strip()) for m in matches}
        return SessionAnalysis(
            goal_alignment=dim_map.get('目标对齐度', ('中', ''))[0],
            closure_index=dim_map.get('闭环指数', ('中', ''))[0],
            flow_depth=dim_map.get('心流深度', ('中', ''))[0],
            cognition_growth=dim_map.get('认知成长', ('中', ''))[0],
            goal_evidence=dim_map.get('目标对齐度', ('', ''))[1],
            closure_evidence=dim_map.get('闭环指数', ('', ''))[1],
            flow_evidence=dim_map.get('心流深度', ('', ''))[1],
            cognition_evidence=dim_map.get('认知成长', ('', ''))[1]
        )

    def _get_goals_text(self, agent_id: str) -> str:
        """读取用户目标（带24h缓存，实体锚点结构）"""
        if not agent_id:
            return "未声明目标"
        try:
            from plugin.goal_extractor import GoalExtractor
            return GoalExtractor().extract(agent_id)
        except Exception:
            return "未声明目标"
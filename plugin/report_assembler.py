import sqlite3, os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

try:
    from plugin.brave_search import BraveSearch
    B = True
except:
    B = False

class ReportAssembler:
    POSITIVE_LABELS = {'四维协同', '高产出模式', '认知突破', '平稳推进', '平淡期'}
    SHORTCUT_LABELS = {'执行卡壳', '目标漂移', '心流不稳', '迷失探索', '舒适区运转', '能量耗尽', '产出饱和', '卡壳 burnout'}
    PORTRAIT_DIM_MAP = {
        '执行卡壳': '闭环指数',
        '目标漂移': '目标对齐',
        '心流不稳': '心流深度',
        '迷失探索': '认知成长',
        '认知突破': '认知成长',
        '舒适区运转': '认知成长',
        '能量耗尽': None,
        '产出饱和': None,
        '卡壳 burnout': None,
    }
    
    def __init__(self, db="data/flow_ecosystem.db"):
        self.db = db
        self.brave = None
        if B and os.getenv('BRAVE_API_KEY'):
            self.brave = BraveSearch(api_key=os.getenv('BRAVE_API_KEY'))
    
    def _scan_distribution(self, sessions, dominant_label):
        from collections import Counter
        
        # 如果 dominant 本身就是短板画像，不触发分布洞察（核心状态已暴露）
        if dominant_label in self.SHORTCUT_LABELS:
            return {
                'has_weakness': False, 'insight': '', 'weak_label': '', 'weak_pct': 0,
                'weak_duration': 0, 'weak_sessions': [], 'weak_summary': '', 'weak_dim': None
            }
        
        label_durations = {}
        total_duration = 0
        
        for s in sessions:
            label = s.get('portrait_label', '未知')
            dur = s.get('session_duration', 600)
            label_durations[label] = label_durations.get(label, 0) + dur
            total_duration += dur
        
        weak_candidates = []
        for label, dur in label_durations.items():
            if label in self.SHORTCUT_LABELS and total_duration > 0:
                pct = dur / total_duration * 100
                if pct > 15:
                    weak_candidates.append({
                        'label': label, 'pct': round(pct, 1), 'duration': dur,
                        'sessions': [s for s in sessions if s.get('portrait_label') == label]
                    })
        
        if weak_candidates:
            weak_candidates.sort(key=lambda x: x['duration'], reverse=True)
            weak = weak_candidates[0]
            h = weak['duration'] // 3600
            m = (weak['duration'] % 3600) // 60
            dur_str = f"{h}小时{m}分钟" if h > 0 and m > 0 else f"{h}小时" if h > 0 else f"{m}分钟"
            insight = f"{weak['pct']}%工作时长（{dur_str}）处于'{weak['label']}'状态，产出质量存在局部振荡"
            
            weak_summary = []
            for s in weak['sessions']:
                sid = s.get('session_id', 'N/A')[:12]
                dur = s.get('session_duration', 600)
                h2 = dur // 3600
                m2 = (dur % 3600) // 60
                dur_str2 = f"{h2}小时{m2}分钟" if h2 > 0 and m2 > 0 else f"{h2}小时" if h2 > 0 else f"{m2}分钟"
                msg = s.get('msg_count', 0)
                weak_summary.append(f"Session {sid}: {dur_str2}, {msg}条消息")
            
            weak_dim = self.PORTRAIT_DIM_MAP.get(weak['label'], None)
            return {
                'has_weakness': True,
                'insight': insight,
                'weak_label': weak['label'],
                'weak_pct': weak['pct'],
                'weak_duration': weak['duration'],
                'weak_sessions': weak['sessions'],
                'weak_summary': "\n".join(weak_summary),
                'weak_dim': weak_dim
            }
        
        return {'has_weakness': False, 'insight': '', 'weak_label': '', 'weak_pct': 0, 'weak_duration': 0, 'weak_sessions': [], 'weak_summary': ''}
    
    def _fmt_duration(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        if h > 0 and m > 0:
            return f"{h}小时{m}分钟"
        elif h > 0:
            return f"{h}小时"
        else:
            return f"{m}分钟"
    
    def _format_trend_distribution(self, trend, volatility, dist=None, dim_name=None):
        """趋势分布列：数学趋势 + 分布洞察（具体事实，不抽象）
        dist: _scan_distribution 返回值
        dim_name: 当前维度名（目标对齐/闭环指数/心流深度/认知成长）"""
        is_low = not volatility or "低波动" in volatility or "平稳" in volatility or "低" in volatility
        
        dist_str = ""
        if dist and dist.get('has_weakness'):
            weak_dim = dist.get('weak_dim')
            if weak_dim is None or weak_dim == dim_name:
                dur = self._fmt_duration(dist.get('weak_duration', 0))
                label = dist.get('weak_label', '')
                dist_str = f"，但{dur}{label}"
        
        if is_low:
            base = trend.replace("稳步提升", "稳步上升").replace("基本持平", "平稳")
            return f"{base}{dist_str}"
        
        direction = trend.replace("稳步提升", "上升").replace("持续下滑", "下降").replace("基本持平", "震荡")
        return f"{direction} · 起伏较大{dist_str}"
    
    def _get_sessions_by_dialog_time(self, start: str, end: str, limit: int = None) -> List[Dict]:
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT session_id, MIN(timestamp) as dialog_time
            FROM sessions
            WHERE timestamp BETWEEN ? AND ?
            AND session_id IS NOT NULL AND session_id != ''
            GROUP BY session_id
        """, (start, end))
        time_map = {r[0]: r[1] for r in c.fetchall()}
        
        if not time_map:
            conn.close()
            return []
        
        session_ids = list(time_map.keys())
        placeholders = ','.join(['?' for _ in session_ids])
        
        dur_sql = """
            SELECT session_id,
                   CAST((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 86400 AS INTEGER) as duration_sec
            FROM sessions
            WHERE session_id IN ({p})
            GROUP BY session_id
        """.format(p=placeholders)
        c.execute(dur_sql, tuple(session_ids))
        duration_map = {r[0]: max(r[1], 60) for r in c.fetchall()}
        
        sql = f"""
            SELECT
                sa.session_id, sa.goal_alignment, sa.closure_index, sa.flow_depth, sa.cognition_growth,
                sa.goal_evidence, sa.closure_evidence, sa.flow_evidence, sa.cognition_evidence,
                sa.portrait_label, sa.portrait_description, sa.portrait_suggestion, sa.portrait_rule_insight,
                sa.created_at
            FROM session_analyses sa
            INNER JOIN (
                SELECT session_id, MAX(created_at) as max_created
                FROM session_analyses
                WHERE session_id IN ({placeholders})
                GROUP BY session_id
            ) latest ON sa.session_id = latest.session_id AND sa.created_at = latest.max_created
            WHERE sa.session_id IN ({placeholders})
        """
        params = session_ids * 2
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        
        c.execute(sql, tuple(params))
        rows = []
        for r in c.fetchall():
            row = dict(r)
            row['dialog_time'] = time_map.get(row['session_id'], start)
            row['session_duration'] = duration_map.get(row['session_id'], 600)
            rows.append(row)
        conn.close()
        return rows
    
    def _get_recent_sessions(self, limit=None) -> List[Dict]:
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        sql = """SELECT sa.session_id, sa.goal_alignment, sa.closure_index, sa.flow_depth, sa.cognition_growth,
            sa.goal_evidence, sa.closure_evidence, sa.flow_evidence, sa.cognition_evidence,
            sa.portrait_label, sa.portrait_description, sa.portrait_suggestion, sa.portrait_rule_insight,
            sa.created_at, 600 as session_duration, sa.created_at as dialog_time
            FROM (
                SELECT sa.* FROM session_analyses sa
                INNER JOIN (
                    SELECT session_id, MAX(created_at) as max_created
                    FROM session_analyses
                    GROUP BY session_id
                ) latest ON sa.session_id = latest.session_id AND sa.created_at = latest.max_created
            ) sa
            WHERE 1=1"""
        if limit:
            sql += " ORDER BY created_at DESC LIMIT ?"
            c.execute(sql, (limit,))
        else:
            sql += " ORDER BY created_at DESC"
            c.execute(sql)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    
    def _aggregate_dimensions(self, sessions):
        M = {'高': 3, '中': 2, '低': 1}
        C = {'目标对齐': 'goal_alignment', '闭环指数': 'closure_index', '心流深度': 'flow_depth', '认知成长': 'cognition_growth'}
        E = {'目标对齐': 'goal_evidence', '闭环指数': 'closure_evidence', '心流深度': 'flow_evidence', '认知成长': 'cognition_evidence'}
        r = {}
        for name, col in C.items():
            ws = tw = 0
            for s in sessions:
                v = s.get(col)
                if not v: continue
                sc = M.get(v, 2)
                w = s.get('session_duration', 600)
                ws += sc * w
                tw += w
            if tw == 0:
                r[name] = {'value': '中', 'evidence': '无数据', 'raw_score': 2.0}
                continue
            a = ws / tw
            v = '高' if a > 2.5 else '中' if a >= 1.5 else '低'
            e = sessions[0].get(E[name], '') or '无证据'
            r[name] = {'value': v, 'evidence': e, 'raw_score': round(a, 2)}
        return r
    
    def _calc_trend(self, sessions):
        import statistics
        M = {'高': 3, '中': 2, '低': 1}
        D = {'目标对齐': 'goal_alignment', '闭环指数': 'closure_index', '心流深度': 'flow_depth', '认知成长': 'cognition_growth'}
        r = {}
        for name, col in D.items():
            vals = [s[col] for s in sessions if s.get(col)]
            if not vals:
                r[name] = {'direction': '→ 平稳', 'volatility': '低波动'}
                continue
            sc = [M.get(v, 2) for v in vals]
            if len(sc) >= 2:
                f, l = sc[-1], sc[0]
                d = '↗ 上升' if l > f else '↘ 下降' if l < f else '→ 平稳'
                m = statistics.mean(sc)
                std = statistics.stdev(sc)
                vol = std / m if m > 0 else 0
            else:
                d, vol = '→ 平稳', 0
            v = '高波动' if vol > 0.5 else '中等波动' if vol > 0.2 else '低波动'
            r[name] = {'direction': d, 'volatility': v}
        return r
    
    def generate_flow_report(self, session_limit=30, trend_limit=30, start=None, end=None):
        if start and end:
            S = self._get_sessions_by_dialog_time(start, end, limit=session_limit)
        else:
            S = self._get_recent_sessions(limit=session_limit)
        
        if not S:
            return "📭 暂无分析数据。"
        
        times = [s.get('dialog_time') or s.get('created_at', '') for s in S if (s.get('dialog_time') or s.get('created_at'))]
        if len(times) >= 2:
            times.sort()
            st, et = times[0][:16], times[-1][:16]
            T = f"{st[:10]} {st[11:]} ~ {et[11:]}" if st[:10] == et[:10] else f"{st} ~ {et}"
        elif len(times) == 1:
            T = times[0][:16]
        else:
            T = datetime.now().strftime("%Y-%m-%d")
        
        from collections import Counter
        labels = [s.get('portrait_label', '未知') for s in S]
        label_counts = Counter(labels)
        majority_label, majority_count = label_counts.most_common(1)[0]
        L = next((s for s in S if s.get('portrait_label') == majority_label), S[0])
        A = self._aggregate_dimensions(S)
        R = self._calc_trend(S)
        P = {'label': L.get('portrait_label', '未知'), 'description': L.get('portrait_description', ''),
             'suggestion': L.get('portrait_suggestion', ''), 'rule_insight': L.get('portrait_rule_insight', '')}

        # 计算分布洞察
        dist = self._scan_distribution(S, L.get('portrait_label', '未知'))
        dist_insight = dist.get('insight', '')
        dist_line = f"⚠️ 分布洞察：{dist_insight}" if dist.get('has_weakness') else ""

        try:
            from plugin.report_polisher import ReportPolisher
            M2 = ReportPolisher().polish(S, P, R, insight=dist.get('insight', ''), weak_summary=dist.get('weak_summary', ''))
        except Exception as e:
            print(f"[A]Polisher: {e}")
            M2 = {'quote': P.get('suggestion', ''), 'performances': [], 'scenes': [], 'suggestion': P.get('suggestion', '')}
        
        X, Y = [], []
        try:
            from plugin.trend_analyzer import TrendAnalyzer
            ta = TrendAnalyzer(self.db)
            if start and end:
                Z = ta.analyze_by_range(limit=trend_limit, start_time=start, end_time=end)
            else:
                Z = ta.analyze_by_range(limit=trend_limit)
            X, Y = Z.get('anomalies', []), Z.get('patterns', [])
        except Exception as e:
            print(f"[A]TrendAnalyzer: {e}")
        
        # 本地提取证据
        K = []
        for s in S:
            ev = s.get('closure_evidence', '') or s.get('goal_evidence', '')
            if ev and len(ev) > 10:
                K.append(ev[:40])
        K = K[:3] if K else ['当前整体状态平稳，无明显卡壳点']
        # 融合TrendAnalyzer异常
        try:
            from plugin.trend_analyzer import TrendAnalyzer
            ta = TrendAnalyzer(self.db)
            if start and end:
                Z = ta.analyze_by_range(limit=trend_limit, start_time=start, end_time=end)
            else:
                Z = ta.analyze_by_range(limit=trend_limit)
            for anomaly in Z.get('anomalies', [])[:3]:
                ev = anomaly.get('evidence', '')
                if ev and ev not in K:
                    K.append(ev[:40])
        except:
            pass
        K = K[:3]
        U = []
        if self.brave:
            try:
                # 修复：搜索关键词结合 portrait_label + stuck_points，避免重复推荐
                search_evidence = P['description']
                if K and K[0] != '当前整体状态平稳，无明显卡壳点':
                    search_evidence += " " + " ".join(K[:2])
                U = self.brave.search_tools(P['label'], search_evidence, count=2)
            except:
                pass
        
        try:
            from plugin.breakthrough_writer import BreakthroughWriter
            if not U: U = []
            W = BreakthroughWriter().write(U, P, K)
        except Exception as e:
            print(f"[A]Writer: {e}")
            W = {'qualitative': f"当前状态为{P.get('label') or '未知'}。",
                 'benefit_time': '工具推荐暂不可用', 'benefit_value': '工具推荐暂不可用',
                 'action_max': '工具推荐暂不可用', 'action_quick': '工具推荐暂不可用'}
        
        E2 = {'目标对齐': '🎯', '闭环指数': '🔄', '心流深度': '🌊', '认知成长': '🧠'}
        tb = ""
        perf_list = M2.get('performances', [])
        dim_idx = {'目标对齐': 0, '闭环指数': 1, '心流深度': 2, '认知成长': 3}
        
        # 计算总时长和分布洞察
        total_dur = self._fmt_duration(sum(s.get('session_duration', 600) for s in S))
        dist = self._scan_distribution(S, L.get('portrait_label', '未知'))
        dist_insight = dist.get('insight', '')
        dist_line = f"⚠️ 分布洞察：{dist_insight}" if dist.get('has_weakness') else ""
        
        for D in ['目标对齐', '闭环指数', '心流深度', '认知成长']:
            V = A[D]['value']
            TR = R.get(D, {})
            DR = TR.get('direction', '→ 平稳')
            VL = TR.get('volatility', '低波动')
            PF_raw = perf_list[dim_idx[D]] if len(perf_list) > dim_idx[D] else None
            if PF_raw:
                PF = PF_raw[:50]
            else:
                dim_evidence_map = {
                    '目标对齐': [s.get('goal_evidence', '') for s in S],
                    '闭环指数': [s.get('closure_evidence', '') for s in S],
                    '心流深度': [s.get('flow_evidence', '') for s in S],
                    '认知成长': [s.get('cognition_evidence', '') for s in S],
                }
                fallback_evs = dim_evidence_map.get(D, [])
                PF = next((e[:50] for e in fallback_evs if e and len(e.strip()) > 10), '数据不足')
            DS = '📈' if '上升' in DR else '📉' if '下降' in DR else '〰️'
            DT = DR.replace('↗ ', '').replace('↘ ', '').replace('→ ', '')
            merged_trend = self._format_trend_distribution(f"{DS} {DT}", VL, dist=dist, dim_name=D)
            tb += f"│ {E2[D]} {D} │ {V}   │ {merged_trend} │ {PF[:50]}                              │\n"
        
        sc = "".join([f"• {C}\n" for C in M2.get('scenes', [])[:3]]) or "• 暂无显著场景记录\n"
        tl = W.get('benefit_time', '工具推荐暂不可用')
        vl = W.get('benefit_value', '工具推荐暂不可用')
        am = W.get('action_max', '工具推荐暂不可用')
        aq = W.get('action_quick', '工具推荐暂不可用')
        ql = W.get('qualitative', '')
        # 动态标题
        if P.get('label') == '四维协同':
            bt_title = '保持与进阶'
        elif P.get('label') == '执行卡壳':
            bt_title = '打破执行卡壳'
        elif P.get('label') == '规划空转':
            bt_title = '聚焦核心交付'
        elif P.get('label') == '认知漂移':
            bt_title = '锚定执行链路'
        else:
            bt_title = f"保持{P.get('label', '当前状态')}"
        
        if U:
            TU = U[0]
            N = TU.get('title', '未知')[:25]
            SO = TU.get('url', '').split('/')[2][:25] if TU.get('url') else '未知来源'
            tool_block = f"🛠 核心工具：{N} (来源: {SO})\n\n⏱ 预期收益：\n  • 时间维度：{tl}\n  • 价值维度：{vl}"
        else:
            tool_block = "🛠 核心工具：基于画像生成通用建议"
        
        return f"""📅 Flow 认知镜像 · {T}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心状态：{P['label']} —— {P['description']}
{dist_line}

> "{M2.get('quote', '')}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 四维雷达（基于全部 {len(S)} 个会话，累计 {total_dur}）

┌──────────┬──────┬────────────────┬────────────────────────────────────────┐
│ 维度     │ 评价 │ 趋势分布       │ 具体表现                              │
├──────────┼──────┼────────────────┼────────────────────────────────────────┤
{tb}└──────────┴──────┴────────────────┴────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 关键行为洞察

基于全部 {len(S)} 个会话的深度分析，{Y[0] if Y else '状态平稳，无明显波动'}。

典型场景：
{sc}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 整体建议

{M2.get('suggestion', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 破局指南：{bt_title}

{ql}

为了降低执行阻力，为你推荐：

{tool_block}

⚡️ 马上行动 (今晚就能做)：

最大回报：{am}
最高性价比：{aq}
"""
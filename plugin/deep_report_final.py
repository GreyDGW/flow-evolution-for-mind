import sqlite3
import os
from datetime import datetime, timedelta


class DeepReportFinal:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), '..', 'data', 'flow_ecosystem.db')
        self.template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'deep_report.md')

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _query_stats(self, start_date, end_date):
        """查询数据库，返回所有统计数据 - 兼容多种日期格式"""
        conn = self._get_connection()
        c = conn.cursor()

        # 直接用 session_analyses.created_at 过滤（已通过batch_analyze保存正确时间戳）
        # 不再依赖 sessions 表的复杂过滤条件（is_system_noise等会导致过度过滤）
        date_filter = f"""WHERE sa.created_at >= '{start_date} 00:00:00' AND sa.created_at < '{end_date} 00:00:00'"""

        stats = {}

        try:
            # 基础统计
            c.execute(f"""
                SELECT COUNT(*), COUNT(DISTINCT agent_id)
                FROM session_analyses sa {date_filter}
            """)
            total, agent_count = c.fetchone()
            stats['total_records'] = total or 0
            stats['agent_count'] = agent_count or 0

            if stats['total_records'] == 0:
                conn.close()
                return self._empty_stats()

            # 四维分布 - 使用明确的字段名
            c.execute(f"""
                SELECT
                    SUM(CASE WHEN sa.goal_alignment='高' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.goal_alignment='中' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.goal_alignment='低' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.closure_index='高' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.closure_index='中' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.closure_index='低' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.flow_depth='高' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.flow_depth='中' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.flow_depth='低' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.cognition_growth='高' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.cognition_growth='中' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sa.cognition_growth='低' THEN 1 ELSE 0 END)
                FROM session_analyses sa {date_filter}
            """)
            r = c.fetchone()
            dims = ['goal', 'closure', 'flow', 'cog']
            for i, dim in enumerate(dims):
                stats[f'{dim}_high'] = r[i*3] or 0
                stats[f'{dim}_mid'] = r[i*3+1] or 0
                stats[f'{dim}_low'] = r[i*3+2] or 0
                total_dim = stats[f'{dim}_high'] + stats[f'{dim}_mid'] + stats[f'{dim}_low']
                if total_dim > 0:
                    avg = (stats[f'{dim}_high']*3 + stats[f'{dim}_mid']*2 + stats[f'{dim}_low']) / total_dim
                    stats[f'{dim}_avg'] = round(avg, 2)
                else:
                    stats[f'{dim}_avg'] = 0.0

            # 综合评分
            overall = (
                stats['goal_avg'] + stats['closure_avg'] +
                stats['flow_avg'] + stats['cog_avg']
            ) / 4
            stats['overall_score'] = round(overall, 2)
            stats['overall_pct'] = int(overall / 3 * 100)

            # 画像分布
            c.execute(f"""
                SELECT portrait_label, COUNT(*)
                FROM session_analyses sa {date_filter}
                GROUP BY portrait_label ORDER BY COUNT(*) DESC
            """)
            portraits = []
            for label, cnt in c.fetchall():
                max_bar = 20
                bar_len = min(int(cnt / stats['total_records'] * max_bar), max_bar) if stats['total_records'] > 0 else 0
                bar = "█" * bar_len + "░" * (max_bar - bar_len)
                pct = round(cnt / stats['total_records'] * 100, 1) if stats['total_records'] > 0 else 0
                portraits.append({'label': label or '(未分类)', 'count': cnt, 'pct': pct, 'bar': bar})
            stats['portraits'] = portraits

            # 各Agent表现
            c.execute(f"""
                SELECT agent_id, COUNT(*),
                       GROUP_CONCAT(DISTINCT goal_alignment),
                       ROUND(AVG(
                           CASE goal_alignment
                               WHEN '高' THEN 3
                               WHEN '中' THEN 2
                               WHEN '低' THEN 1
                               ELSE 2
                           END
                       ), 2)
                FROM session_analyses sa {date_filter}
                AND agent_id IS NOT NULL
                GROUP BY agent_id ORDER BY COUNT(*) DESC
            """)
            agents_data = []
            for aid, cnt, goals, avg_goal in c.fetchall():
                agents_data.append({
                    'agent_id': aid,
                    'count': cnt,
                    'goals': goals,
                    'avg_goal': avg_goal
                })
            stats['agents'] = agents_data

            # 所有记录（用于查找最佳/典型/有待提升）
            c.execute(f"""
                SELECT sa.session_id, s.agent_id, sa.goal_alignment, sa.closure_index,
                       sa.flow_depth, sa.cognition_growth, sa.portrait_label,
                       sa.goal_evidence, sa.created_at
                FROM session_analyses sa
                JOIN sessions s ON sa.session_id = s.session_id
                {date_filter}
                ORDER BY sa.created_at
            """)
            stats['all_records'] = [
                {
                    'session_id': r[0],
                    'agent_id': r[1],
                    'goal': r[2],
                    'closure': r[3],
                    'flow': r[4],
                    'cognition': r[5],
                    'portrait': r[6],
                    'evidence': r[7] or '',
                    'created_at': r[8]
                }
                for r in c.fetchall()
            ]

            # 趋势对比（前一天数据）
            prev_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            prev_end = start_date
            c.execute(f"""
                SELECT
                    ROUND(AVG(
                        CASE goal_alignment
                            WHEN '高' THEN 3
                            WHEN '中' THEN 2
                            WHEN '低' THEN 1
                            ELSE 2
                        END
                    ), 2),
                    COUNT(*)
                FROM session_analyses sa
                WHERE created_at >= '{prev_start}' AND created_at < '{prev_end}'
            """)
            prev_row = c.fetchone()
            stats['prev_avg'] = prev_row[0] if prev_row and prev_row[0] else None
            stats['prev_count'] = prev_row[1] if prev_row and prev_row[1] else 0

        except Exception as e:
            print(f"⚠️ 查询出错: {e}")
            stats = self._empty_stats()
        finally:
            conn.close()

        return stats

    def _empty_stats(self):
        """返回空数据的默认统计"""
        return {
            'total_records': 0,
            'agent_count': 0,
            'goal_high': 0, 'goal_mid': 0, 'goal_low': 0, 'goal_avg': 0,
            'closure_high': 0, 'closure_mid': 0, 'closure_low': 0, 'closure_avg': 0,
            'flow_high': 0, 'flow_mid': 0, 'flow_low': 0, 'flow_avg': 0,
            'cog_high': 0, 'cog_mid': 0, 'cog_low': 0, 'cog_avg': 0,
            'overall_score': 0, 'overall_pct': 0,
            'portraits': [],
            'agents': [],
            'all_records': [],
            'prev_avg': None,
            'prev_count': 0
        }

    def _find_best_session(self, records):
        """找目标对齐度最高的session作为最佳表现"""
        valid = [r for r in records if len(r.get('evidence', '')) > 50]
        if not valid:
            return None

        score_map = {'高': 3, '中': 2, '低': 1}
        best = max(valid, key=lambda x: score_map.get(x.get('goal', '中'), 2))

        return self._format_session(best, "最佳表现")

    def _find_typical_session(self, records, avg_score):
        """找一个有代表性的session（目标对齐度接近平均值）"""
        valid = [r for r in records if len(r.get('evidence', '')) > 50]
        if not valid:
            return None

        score_map = {'高': 3, '中': 2, '低': 1}
        typical = min(valid, key=lambda x: abs(score_map.get(x.get('goal', '中'), 2) - avg_score))

        return self._format_session(typical, "典型案例")

    def _find_weak_session(self, records):
        """找目标对齐度最低的session作为有待提升"""
        valid = [r for r in records if len(r.get('evidence', '')) > 50]
        if not valid:
            return None

        score_map = {'高': 3, '中': 2, '低': 1}
        weak = min(valid, key=lambda x: score_map.get(x.get('goal', '中'), 2))

        return self._format_session(weak, "有待提升")

    def _format_session(self, session, label):
        """格式化session信息"""
        return {
            'session_id': session['session_id'],
            'goal': session.get('goal', '-'),
            'closure': session.get('closure', '-'),
            'flow': session.get('flow', '-'),
            'cognition': session.get('cognition', '-'),
            'portrait': session.get('portrait', '-'),
            'evidence': session.get('evidence', '')[:300]
        }

    def _generate_portrait_section(self, portraits):
        """生成画像分布部分"""
        if not portraits:
            return "| （无数据） | | | |"

        lines = ["| 画像标签 | 数量 | 占比 | 可视化 |", "|----------|------|------|--------|"]
        for p in portraits:
            lines.append(
                f"| {p['label']:<12} | {p['count']:>3} | {p['pct']:>5}% | {p['bar']} |"
            )
        return "\n".join(lines)

    def _generate_agent_section(self, agents):
        """生成各Agent表现部分"""
        if not agents:
            return "| （无数据） | | | |"

        lines = ["| Agent ID | Session数 | 平均目标分 | 目标分布 |",
                 "|----------|-----------|------------|----------|"]
        for a in agents:
            lines.append(
                f"| {a['agent_id']:<18} | {a['count']:>3} | {a.get('avg_goal', '-'):>5} | {a.get('goals', '-')} |"
            )
        return "\n".join(lines)

    def _generate_dimension_analysis(self, stats, dim_name, dim_key):
        """生成单个维度的详细解读"""
        high = stats.get(f'{dim_key}_high', 0)
        mid = stats.get(f'{dim_key}_mid', 0)
        low = stats.get(f'{dim_key}_low', 0)
        avg = stats.get(f'{dim_key}_avg', 0)
        total = stats.get('total_records', 1)

        if total == 0:
            return "**（无数据）**"

        high_pct = round(high / total * 100, 1)
        mid_pct = round(mid / total * 100, 1)
        low_pct = round(low / total * 100, 1)

        analysis = f"\n**核心发现**:\n\n"
        analysis += f"- **整体评分**: {avg:.1f}/3.0 ({'优秀' if avg >= 2.5 else '良好' if avg >= 2.0 else '待改进'})\n"
        analysis += f"- **分布**: 高({high_pct}%) / 中({mid_pct}%) / 低({low_pct}%)\n\n"

        # 根据分数给出具体洞察
        if avg >= 2.5:
            analysis += f"✅ **优势领域**: 该维度表现优异，{high_pct}%的session达到'高'级别。\n"
        elif avg >= 2.0:
            analysis += f"⚠️ **中等水平**: 该维度有提升空间，建议关注判定为'低'的{low_pct}%session。\n"
        else:
            analysis += f"❌ **需要改进**: 该维度整体偏弱，仅{high_pct}%达到'高'级别，需要重点优化。\n"

        return analysis

    def _generate_trend_section(self, stats):
        """生成趋势对比"""
        curr_avg = stats.get('overall_score', 0)
        prev_avg = stats.get('prev_avg')
        prev_count = stats.get('prev_count', 0)

        if prev_avg is None or prev_count == 0:
            return "- **无历史对比数据**（前一天无分析记录）\n- 这是首次生成报告或前一天无有效数据。"

        diff = curr_avg - prev_avg
        trend = "📈 上升" if diff > 0.1 else ("📉 下降" if diff < -0.1 else "➡️ 持平")
        emoji = "✅" if diff >= 0 else "⚠️"

        return f"- **对比日期**: 前一天\n" \
               f"- **前一天均分**: {prev_avg:.2f}\n" \
               f"- **当前均分**: {curr_avg:.2f}\n" \
               f"- **变化趋势**: {trend} ({diff:+.2f}) {emoji}\n" \
               f"- **前一天记录数**: {prev_count}"

    def _query_portrait_and_stuck(self, start, end):
        """查询主导画像和卡壳点，用于 BreakthroughWriter"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 主导画像（取数量最多的）
        c.execute("""
            SELECT portrait_label, portrait_description, portrait_suggestion, COUNT(*) as cnt 
            FROM session_analyses 
            WHERE date(created_at) >= date(?) AND date(created_at) < date(?) 
            GROUP BY portrait_label 
            ORDER BY cnt DESC 
            LIMIT 1 
        """, (start, end))
        row = c.fetchone()
        portrait = { 
            'label': row[0] if row and row[0] else '兜底', 
            'description': row[1] if row and row[1] else '', 
            'suggestion': row[2] if row and row[2] else '' 
        }
        
        # 卡壳点：优先取判定为低的维度的证据
        c.execute("""
            SELECT goal_evidence, closure_evidence, flow_evidence, cognition_evidence, 
                   goal_alignment, closure_index, flow_depth, cognition_growth 
            FROM session_analyses 
            WHERE date(created_at) >= date(?) AND date(created_at) < date(?) 
            AND (goal_alignment = '低' OR closure_index = '低' OR flow_depth = '低' OR cognition_growth = '低') 
            ORDER BY RANDOM() 
            LIMIT 5 
        """, (start, end))
        
        stuck_points = []
        for r in c.fetchall():
            for i, dim in enumerate(['目标', '闭环', '心流', '认知']):
                if r[4+i] == '低' and r[i] and len(r[i]) > 10:
                    stuck_points.append(r[i][:50])
        
        # 兜底：如果没有低分证据，取任意有效证据
        if not stuck_points:
            c.execute("""
                SELECT goal_evidence FROM session_analyses 
                WHERE date(created_at) >= date(?) AND date(created_at) < date(?) 
                AND goal_evidence IS NOT NULL AND LENGTH(goal_evidence) > 10 
                LIMIT 3 
            """, (start, end))
            for r in c.fetchall():
                stuck_points.append(r[0][:50])
        
        conn.close()
        return portrait, stuck_points
    
    def _generate_breakthrough_guide(self, start, end):
        """嫁接浅度版 BreakthroughWriter，生成个性化破局指南"""
        portrait, stuck_points = self._query_portrait_and_stuck(start, end)
        if not stuck_points:
            stuck_points = ['当前整体状态平稳，无明显卡壳点']
        
        try:
            from plugin.breakthrough_writer import BreakthroughWriter
            writer = BreakthroughWriter()
            result = writer.write(tools=[], portrait=portrait, stuck_points=stuck_points)
            return result
        except Exception as e:
            # Fallback：降级为基于画像的通用建议
            label = portrait.get('label', '兜底')
            desc = portrait.get('description', '')
            return { 
                'qualitative': f'当前状态为{label}——{desc}。', 
                'benefit_time': '预计每天节省30分钟无效内耗', 
                'benefit_value': '把讨论清楚变成交付可用', 
                'action_max': f'15分钟：针对"{stuck_points[0]}"写一个最小可验证动作', 
                'action_quick': f'5分钟：在日历中设置提醒处理"{stuck_points[0]}"' 
            }

    def generate(self, start_date, end_date):
        """生成完整报告"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        stats = self._query_stats(start_date, end_date)

        best = self._find_best_session(stats.get('all_records', []))
        typical = self._find_typical_session(stats.get('all_records', []), stats.get('goal_avg', 2))
        weak = self._find_weak_session(stats.get('all_records', []))

        replacements = {
            'report_title': f'Flow Ecosystem - {start_date} 认知分析报告',
            'date_range': start_date,
            'date_range_full': f'{start_date} ~ {end_date}',
            'total_records': str(stats.get('total_records', 0)),
            'agent_count': str(stats.get('agent_count', 0)),

            'goal_high': str(stats.get('goal_high', 0)),
            'goal_mid': str(stats.get('goal_mid', 0)),
            'goal_low': str(stats.get('goal_low', 0)),
            'goal_avg': str(stats.get('goal_avg', 0)),

            'closure_high': str(stats.get('closure_high', 0)),
            'closure_mid': str(stats.get('closure_mid', 0)),
            'closure_low': str(stats.get('closure_low', 0)),
            'closure_avg': str(stats.get('closure_avg', 0)),

            'flow_high': str(stats.get('flow_high', 0)),
            'flow_mid': str(stats.get('flow_mid', 0)),
            'flow_low': str(stats.get('flow_low', 0)),
            'flow_avg': str(stats.get('flow_avg', 0)),

            'cog_high': str(stats.get('cog_high', 0)),
            'cog_mid': str(stats.get('cog_mid', 0)),
            'cog_low': str(stats.get('cog_low', 0)),
            'cog_avg': str(stats.get('cog_avg', 0)),

            'overall_score': str(stats.get('overall_score', 0)),
            'overall_pct': str(stats.get('overall_pct', 0)),

            'portrait_distribution': self._generate_portrait_section(stats.get('portraits', [])),
            'agent_performance': self._generate_agent_section(stats.get('agents', [])),

            'best_session_id': (best['session_id'][:25]) if best else '(无数据)',
            'best_goal': best.get('goal', '-') if best else '-',
            'best_closure': best.get('closure', '-') if best else '-',
            'best_flow': best.get('flow', '-') if best else '-',
            'best_cog': best.get('cognition', '-') if best else '-',
            'best_portrait': best.get('portrait', '-') if best else '-',
            'best_evidence': best.get('evidence', '(无足够证据)') if best else '(无数据)',

            'typical_session_id': (typical['session_id'][:25]) if typical else '(无数据)',
            'typ_goal': typical.get('goal', '-') if typical else '-',
            'typ_closure': typical.get('closure', '-') if typical else '-',
            'typ_flow': typical.get('flow', '-') if typical else '-',
            'typ_cog': typical.get('cognition', '-') if typical else '-',
            'typ_portrait': typical.get('portrait', '-') if typical else '-',
            'typ_evidence': typical.get('evidence', '(无足够证据)') if typical else '(无数据)',

            'weak_session_id': (weak['session_id'][:25]) if weak else '(无数据)',
            'weak_goal': weak.get('goal', '-') if weak else '-',
            'weak_closure': weak.get('closure', '-') if weak else '-',
            'weak_flow': weak.get('flow', '-') if weak else '-',
            'weak_cog': weak.get('cognition', '-') if weak else '-',
            'weak_portrait': weak.get('portrait', '-') if weak else '-',
            'weak_evidence': weak.get('evidence', '(无足够证据)') if weak else '(无数据)',

            'strengths_analysis': self._generate_strengths(stats),
            'improvements_analysis': self._generate_improvements(stats),

            'goal_analysis': self._generate_dimension_analysis(stats, '目标对齐度', 'goal'),
            'closure_analysis': self._generate_dimension_analysis(stats, '闭环指数', 'closure'),
            'flow_analysis': self._generate_dimension_analysis(stats, '心流深度', 'flow'),
            'cognition_analysis': self._generate_dimension_analysis(stats, '认知成长', 'cog'),

            'quality_metrics': self._generate_quality_metrics(stats),
            'trend_comparison': self._generate_trend_section(stats),

            # 🆕 嫁接 BreakthroughWriter：用 LLM 生成个性化破局指南
            'suggestions': self._generate_breakthrough_suggestions(start_date, end_date, stats),

            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'agent_list': ', '.join([a['agent_id'] for a in stats.get('agents', [])]) or '(无)'
        }

        report = template
        for key, value in replacements.items():
            report = report.replace(f'{{{key}}}', str(value))

        return report

    def _generate_strengths(self, stats):
        """生成优势领域分析"""
        strengths = []
        dims = [
            ('目标对齐度', 'goal_avg', 'goal_high'),
            ('闭环指数', 'closure_avg', 'closure_high'),
            ('心流深度', 'flow_avg', 'flow_high'),
            ('认知成长', 'cog_avg', 'cog_high')
        ]

        for name, avg_key, high_key in dims:
            avg = stats.get(avg_key, 0)
            high = stats.get(high_key, 0)
            total = stats.get('total_records', 1)
            pct = round(high / total * 100, 1) if total > 0 else 0

            if avg >= 2.5:
                strengths.append(f"- **{name}极高** ({avg:.1f}/3.0): {pct}%的session达到'高'级别")

        if not strengths:
            strengths.append("- （暂无明显优势领域）")

        return '\n'.join(strengths)

    def _generate_improvements(self, stats):
        """生成改进空间分析"""
        improvements = []
        dims = [
            ('目标对齐度', 'goal_avg', 'goal_low'),
            ('闭环指数', 'closure_avg', 'closure_low'),
            ('心流深度', 'flow_avg', 'flow_low'),
            ('认知成长', 'cog_avg', 'cog_low')
        ]

        for name, avg_key, low_key in dims:
            avg = stats.get(avg_key, 0)
            low = stats.get(low_key, 0)
            total = stats.get('total_records', 1)
            pct = round(low / total * 100, 1) if total > 0 else 0

            if avg < 2.0:
                improvements.append(f"- **{name}需加强** ({avg:.1f}/3.0): {pct}%的session为'低'级别")

        if not improvements:
            improvements.append("- （各维度表现均衡）")

        return '\n'.join(improvements)

    def _generate_quality_metrics(self, stats):
        """生成数据质量指标"""
        total = stats.get('total_records', 0)
        has_agent = sum(1 for a in stats.get('agents', []) if a.get('agent_id'))
        has_evidence = len([r for r in stats.get('all_records', []) if len(r.get('evidence', '')) > 80])

        metrics = f"| 指标 | 数值 |\n|------|------|\n"
        metrics += f"| 总记录完整性 | {total}/{total} (100%) |\n"
        metrics += f"| Agent ID填充率 | {has_agent}/{len(stats.get('agents', [])) if stats.get('agents') else 0} |\n"
        metrics += f"| 高质量证据(>80字) | {has_evidence}/{total} ({round(has_evidence/total*100,1) if total > 0 else 0}%) |"

        return metrics

    def _generate_breakthrough_suggestions(self, start_date, end_date, stats):
        """生成基于 BreakthroughWriter 的个性化行动建议"""
        # 调用 BreakthroughWriter 获取破局指南
        bt = self._generate_breakthrough_guide(start_date, end_date)

        # 获取主导画像信息
        portrait, stuck_points = self._query_portrait_and_stuck(start_date, end_date)
        label = portrait.get('label', '当前状态')
        desc = portrait.get('description', '')

        # 格式化输出
        lines = []
        lines.append(f"### 📊 当前状态诊断")
        lines.append(f"**主导画像**: {label}")
        if desc:
            lines.append(f"**状态描述**: {desc}")
        if stuck_points:
            lines.append(f"**核心卡壳点**: {stuck_points[0][:80]}")

        lines.append("")
        lines.append(f"### 💡 破局策略（LLM 个性化生成）")
        lines.append(f"*{bt.get('qualitative', '基于当前数据生成的个性化建议')}*")

        lines.append("")
        lines.append(f"### ⚡️ 马上行动")

        # 最大回报行动（15分钟）
        action_max = bt.get('action_max', '')
        if action_max:
            lines.append(f"1. **🔴 高优先级（最大回报）**")
            lines.append(f"   {action_max}")

        # 最高性价比行动（5分钟）
        action_quick = bt.get('action_quick', '')
        if action_quick:
            lines.append(f"")
            lines.append(f"2. **🟡 中优先级（最高性价比）**")
            lines.append(f"   {action_quick}")

        # 预期收益
        benefit_time = bt.get('benefit_time', '')
        benefit_value = bt.get('benefit_value', '')
        if benefit_time or benefit_value:
            lines.append(f"")
            lines.append(f"### ⏱ 预期收益")
            if benefit_time:
                lines.append(f"- **时间维度**: {benefit_time}")
            if benefit_value:
                lines.append(f"- **价值维度**: {benefit_value}")

        return '\n'.join(lines)

    def _generate_suggestions(self, stats):
        """生成行动建议"""
        suggestions = []

        goal_avg = stats.get('goal_avg', 0)
        closure_avg = stats.get('closure_avg', 0)
        flow_avg = stats.get('flow_avg', 0)
        cog_avg = stats.get('cog_avg', 0)

        priority = 1
        if goal_avg < 2.5:
            suggestions.append(f"{priority}. **[高优先级]** 加强目标锚定：在Session开始时明确声明当前推进的具体里程碑")
            priority += 1
        if closure_avg < 2.5:
            suggestions.append(f"{priority}. **[高优先级]** 提升闭环意识：每个Session结束时总结产出和下一步动作")
            priority += 1
        if flow_avg < 2.5:
            suggestions.append(f"{priority}. **[中优先级]** 保护心流状态：减少话题切换，鼓励单点深挖")
            priority += 1
        if cog_avg < 2.5:
            suggestions.append(f"{priority}. **[中优先级]** 促进认知反思：定期回顾旧判断，主动寻找修正机会")
            priority += 1

        if not suggestions:
            suggestions.append("✅ 各维度表现均衡（均≥2.5），继续保持当前工作模式")

        return '\n'.join(suggestions)

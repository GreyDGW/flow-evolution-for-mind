from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import sqlite3
import random

class HistoryAnalyzer:
    def __init__(self, db_path: str = 'flow_ecosystem.db'):
        self.db_path = db_path
        self.local_rules = self._load_local_rules()
    
    def _load_local_rules(self) -> List[Dict]:
        """加载本地规则引擎"""
        return [
            {'name': 'goal_learning', 'pattern': ['学习', '学', '掌握', '学会'], 'type': 'goal', 'category': 'learning'},
            {'name': 'goal_creating', 'pattern': ['创建', '建立', '开发', '编写', '做'], 'type': 'goal', 'category': 'creation'},
            {'name': 'goal_completing', 'pattern': ['完成', '做完', '搞定', '实现'], 'type': 'goal', 'category': 'completion'},
            {'name': 'goal_modifying', 'pattern': ['修改', '调整', '优化', '改进'], 'type': 'goal', 'category': 'modification'},
            {'name': 'pdca_plan', 'pattern': ['计划', '打算', '规划', '准备'], 'type': 'pdca', 'stage': 'plan'},
            {'name': 'pdca_do', 'pattern': ['做', '执行', '进行', '实施'], 'type': 'pdca', 'stage': 'do'},
            {'name': 'pdca_check', 'pattern': ['检查', '验证', '检验', '回顾'], 'type': 'pdca', 'stage': 'check'},
            {'name': 'pdca_adjust', 'pattern': ['调整', '修改', '优化', '改进'], 'type': 'pdca', 'stage': 'adjust'},
            {'name': 'flow_focus', 'pattern': ['专注', '集中', '沉浸', '心流'], 'type': 'flow', 'state': 'focus'},
            {'name': 'flow_interrupt', 'pattern': ['打断', '中断', '分心', '打扰'], 'type': 'flow', 'state': 'interrupt'},
            {'name': 'evolution_positive', 'pattern': ['学会', '掌握', '理解', '进步'], 'type': 'evolution', 'direction': 'positive'},
            {'name': 'evolution_negative', 'pattern': ['忘记', '困惑', '不懂', '卡住'], 'type': 'evolution', 'direction': 'negative'},
        ]
    
    def _group_by_conversation(self, days: int = 7) -> List[List[Dict]]:
        """按会话分组历史数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        cursor.execute("""
            SELECT id, role, content_text, timestamp 
            FROM sessions 
            WHERE timestamp > ? 
            ORDER BY timestamp
        """, (cutoff_time,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        
        # 按时间间隔分组（15分钟超时）
        conversations = []
        current_conversation = []
        last_timestamp = None
        
        for msg in messages:
            # 将时间戳字符串转换为float
            try:
                msg['timestamp'] = float(msg['timestamp'])
            except:
                msg['timestamp'] = datetime.now().timestamp()
            
            if last_timestamp is None:
                current_conversation.append(msg)
            else:
                time_diff = msg['timestamp'] - last_timestamp
                if time_diff > 15 * 60:  # 15分钟超时
                    conversations.append(current_conversation)
                    current_conversation = [msg]
                else:
                    current_conversation.append(msg)
            last_timestamp = msg['timestamp']
        
        if current_conversation:
            conversations.append(current_conversation)
        
        return conversations
    
    def local_scan(self, conversations: List[List[Dict]]) -> List[Dict]:
        """本地快速扫描：使用规则引擎分析"""
        results = []
        
        for conv in conversations:
            analysis = {
                'conversation_id': conv[0]['id'] if conv else 0,
                'goals': [],
                'pdca_stages': [],
                'flow_states': [],
                'evolution_signals': [],
                'confidence': 0.7  # 本地分析置信度
            }
            
            for msg in conv:
                content = msg['content']
                if content is None or content == '':
                    continue
                for rule in self.local_rules:
                    for pattern in rule['pattern']:
                        if pattern in content:
                            if rule['type'] == 'goal':
                                analysis['goals'].append({
                                    'text': content[:50],
                                    'category': rule['category'],
                                    'source': 'local_rule'
                                })
                            elif rule['type'] == 'pdca':
                                analysis['pdca_stages'].append(rule['stage'])
                            elif rule['type'] == 'flow':
                                analysis['flow_states'].append(rule['state'])
                            elif rule['type'] == 'evolution':
                                analysis['evolution_signals'].append(rule['direction'])
            
            # 去重
            analysis['pdca_stages'] = list(set(analysis['pdca_stages']))
            analysis['flow_states'] = list(set(analysis['flow_states']))
            analysis['evolution_signals'] = list(set(analysis['evolution_signals']))
            
            results.append(analysis)
        
        return results
    
    def sample_for_cloud(self, conversations: List[List[Dict]], sample_rate: float = 0.1) -> List[List[Dict]]:
        """抽样选择需要云端分析的对话"""
        # 优先选择复杂对话
        complex_conversations = []
        simple_conversations = []
        
        for conv in conversations:
            # 判断复杂度：消息数量、长度、多样性
            msg_count = len(conv)
            total_length = sum(len(msg['content']) for msg in conv if msg['content'] is not None)
            roles = set(msg['role'] for msg in conv if msg['role'] is not None)
            
            if msg_count > 5 or total_length > 500 or len(roles) > 1:
                complex_conversations.append(conv)
            else:
                simple_conversations.append(conv)
        
        # 复杂对话抽样50%
        complex_sample = random.sample(complex_conversations, max(1, int(len(complex_conversations) * 0.5)))
        
        # 简单对话抽样10%
        simple_sample = random.sample(simple_conversations, max(0, int(len(simple_conversations) * 0.1)))
        
        return complex_sample + simple_sample
    
    def cloud_analyze(self, conversations: List[List[Dict]]) -> List[Dict]:
        """模拟云端分析（实际调用云端LLM）"""
        results = []
        
        for conv in conversations:
            # 模拟云端分析结果
            analysis = {
                'conversation_id': conv[0]['id'] if conv else 0,
                'goals': [],
                'closure_score': random.uniform(0, 100),
                'flow_depth': random.uniform(0, 1),
                'evolution_score': random.uniform(-1, 1),
                'confidence': 0.95,  # 云端分析置信度
                'source': 'cloud_llm'
            }
            
            # 提取目标（模拟LLM输出）
            for msg in conv:
                if msg['role'] == 'user':
                    content = msg['content']
                    if any(p in content for p in ['我想', '我要', '帮我', '学习', '创建']):
                        analysis['goals'].append({
                            'text': content[:50],
                            'time_horizon': 'short',
                            'confidence': 0.8
                        })
            
            results.append(analysis)
        
        return results
    
    def merge_results(self, local_results: List[Dict], cloud_results: List[Dict]) -> List[Dict]:
        """合并本地和云端分析结果"""
        merged = []
        
        # 创建云端结果索引
        cloud_index = {r['conversation_id']: r for r in cloud_results}
        
        for local in local_results:
            conv_id = local['conversation_id']
            
            if conv_id in cloud_index:
                # 优先使用云端结果
                cloud = cloud_index[conv_id]
                merged.append({
                    'conversation_id': conv_id,
                    'goals': cloud.get('goals', local['goals']),
                    'pdca_stages': local['pdca_stages'],
                    'flow_states': local['flow_states'],
                    'evolution_signals': local['evolution_signals'],
                    'closure_score': cloud.get('closure_score', 0),
                    'flow_depth': cloud.get('flow_depth', 0),
                    'evolution_score': cloud.get('evolution_score', 0),
                    'confidence': cloud.get('confidence', local['confidence']),
                    'analysis_source': 'cloud'
                })
            else:
                # 使用本地结果
                merged.append({
                    'conversation_id': conv_id,
                    'goals': local['goals'],
                    'pdca_stages': local['pdca_stages'],
                    'flow_states': local['flow_states'],
                    'evolution_signals': local['evolution_signals'],
                    'closure_score': self._calculate_closure_score(local),
                    'flow_depth': self._calculate_flow_depth(local),
                    'evolution_score': self._calculate_evolution_score(local),
                    'confidence': local['confidence'],
                    'analysis_source': 'local'
                })
        
        return merged
    
    def _calculate_closure_score(self, analysis: Dict) -> float:
        """基于本地分析计算闭环分数"""
        stages = analysis['pdca_stages']
        if not stages:
            return 0
        return len(stages) / 4 * 100
    
    def _calculate_flow_depth(self, analysis: Dict) -> float:
        """基于本地分析计算心流深度"""
        states = analysis['flow_states']
        if 'focus' in states and 'interrupt' not in states:
            return 0.7
        elif 'focus' in states:
            return 0.4
        return 0.2
    
    def _calculate_evolution_score(self, analysis: Dict) -> float:
        """基于本地分析计算认知进化分数"""
        signals = analysis['evolution_signals']
        if not signals:
            return 0
        positive = signals.count('positive')
        negative = signals.count('negative')
        return (positive - negative) / max(len(signals), 1)
    
    def analyze_history(self, days: int = 7, sample_rate: float = 0.1) -> Tuple[List[Dict], int, int]:
        """完整的历史数据分析流程"""
        print(f"🔍 开始分析过去{days}天的历史数据...")
        
        # 步骤1：分组会话
        conversations = self._group_by_conversation(days)
        print(f"📊 共找到 {len(conversations)} 个会话")
        
        # 步骤2：本地快速扫描
        local_results = self.local_scan(conversations)
        print(f"✅ 本地扫描完成")
        
        # 步骤3：抽样选择云端分析
        sample_conversations = self.sample_for_cloud(conversations, sample_rate)
        print(f"☁️ 选择 {len(sample_conversations)} 个会话进行云端分析")
        
        # 步骤4：云端深度分析
        cloud_results = self.cloud_analyze(sample_conversations)
        print(f"✅ 云端分析完成")
        
        # 步骤5：合并结果
        merged_results = self.merge_results(local_results, cloud_results)
        print(f"🔄 结果合并完成")
        
        return merged_results, len(conversations), len(sample_conversations)
    
    def save_results(self, results: List[Dict]):
        """保存分析结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_results 
                (conversation_id, goals_json, pdca_stages, flow_states, 
                 evolution_signals, closure_score, flow_depth, evolution_score, 
                 confidence, analysis_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['conversation_id'],
                str(result['goals']),
                ','.join(result['pdca_stages']),
                ','.join(result['flow_states']),
                ','.join(result['evolution_signals']),
                result['closure_score'],
                result['flow_depth'],
                result['evolution_score'],
                result['confidence'],
                result['analysis_source']
            ))
        
        conn.commit()
        conn.close()
        print(f"💾 已保存 {len(results)} 条分析结果")


# 测试
if __name__ == '__main__':
    analyzer = HistoryAnalyzer()
    results, total_convs, sampled_convs = analyzer.analyze_history(days=7, sample_rate=0.1)
    
    print("\n" + "=" * 70)
    print("📊 分析报告")
    print("=" * 70)
    print(f"总会话数: {total_convs}")
    print(f"云端分析数: {sampled_convs} ({sampled_convs/total_convs*100:.1f}%)")
    print(f"本地分析数: {total_convs - sampled_convs} ({(total_convs-sampled_convs)/total_convs*100:.1f}%)")
    
    # 统计指标
    avg_closure = sum(r['closure_score'] for r in results) / len(results)
    avg_flow = sum(r['flow_depth'] for r in results) / len(results)
    avg_evolution = sum(r['evolution_score'] for r in results) / len(results)
    
    print(f"\n平均闭环分数: {avg_closure:.1f}")
    print(f"平均心流深度: {avg_flow:.2f}")
    print(f"平均认知进化: {avg_evolution:.2f}")
    
    # 保存结果
    analyzer.save_results(results)
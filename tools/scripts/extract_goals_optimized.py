#!/usr/bin/env python3
"""优化版目标提取算法 - 语义分析增强版"""

from datetime import datetime
from typing import List, Optional, Dict
import re
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    role = Column(String(32))
    content_text = Column(Text)
    timestamp = Column(DateTime)

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True)
    declared_text = Column(Text)
    declared_at = Column(DateTime)
    status = Column(String(32))
    drift_score = Column(Float)
    last_mentioned = Column(DateTime)
    closed_at = Column(DateTime)
    closure_evidence = Column(Text)
    complexity_score = Column(Float)

# 目标动词列表
GOAL_VERBS = [
    '创建', '完成', '实现', '达成', '解决', '学习', '掌握', '开发', 
    '设计', '构建', '优化', '更新', '改进', '修复', '集成', '部署',
    '研究', '分析', '评估', '测试', '验证', '实现', '编写', '整理',
    'create', 'build', 'develop', 'implement', 'learn', 'solve', 
    'optimize', 'update', 'improve', 'fix', 'integrate', 'deploy',
    'research', 'analyze', 'evaluate', 'test', 'validate', 'write', 'organize'
]

# 目标关键词
GOAL_KEYWORDS = ['目标', '任务', '计划', '目的', '项目', '工程', '功能', '模块',
                 'goal', 'task', 'plan', 'project', 'feature', 'module']

# 过滤词（表示非目标的词）
FILTER_WORDS = ['是什么', '什么是', '什么叫', '为什么', '怎么样', '如何',
                '谁', '哪里', '何时', '多少', '哪个', '哪些',
                'what', 'why', 'how', 'who', 'where', 'when', 'which']

def contains_filter_word(text: str) -> bool:
    """检查是否包含疑问词（表示提问而非目标）"""
    for word in FILTER_WORDS:
        if word in text:
            return True
    return False

def contains_goal_verb(text: str) -> bool:
    """检查是否包含目标动词"""
    for verb in GOAL_VERBS:
        if verb.lower() in text.lower():
            return True
    return False

def is_json_or_code(text: str) -> bool:
    """检测是否为JSON或代码片段"""
    text = text.strip()
    # JSON检测
    if text.startswith('{') and text.endswith('}') and text.count('{') == text.count('}'):
        return True
    if text.startswith('[') and text.endswith(']') and text.count('[') == text.count(']'):
        return True
    # 代码特征
    code_keywords = ['import', 'def ', 'function ', 'class ', 'const ', 'var ', 'let ', '=>']
    for kw in code_keywords:
        if kw in text:
            return True
    return False

def is_table_fragment(text: str) -> bool:
    """检测是否为表格片段"""
    # 包含表格分隔符
    if text.count('|') >= 3:
        return True
    # 包含大量等号或短横线（分隔线）
    if re.search(r'[-=]{10,}', text):
        return True
    return False

def is_valid_goal(text: str) -> bool:
    """判断是否为有效的目标声明"""
    text = text.strip()
    
    # 长度检查
    if len(text) < 6 or len(text) > 180:
        return False
    
    # 排除JSON/代码
    if is_json_or_code(text):
        return False
    
    # 排除表格片段
    if is_table_fragment(text):
        return False
    
    # 排除纯数字或符号
    if re.match(r'^[\d\s.,;:!?\-\|]+$', text):
        return False
    
    # 排除提问（包含疑问词）
    if contains_filter_word(text):
        return False
    
    # 必须包含至少一个目标动词
    if not contains_goal_verb(text):
        return False
    
    # 至少包含一个中文字符或字母
    if not re.search(r'[\u4e00-\u9fa5a-zA-Z]', text):
        return False
    
    return True

def extract_goals_from_text(text: str) -> List[str]:
    """优化版目标提取 - 语义分析增强"""
    patterns = [
        # 中文目标模式
        r'(?:我想|我要|我需要|我打算|我希望|我计划)(?:\s+)([^\n。！？；]{6,120})',
        r'(?:目标是|目的是|任务是|计划是|计划做)(?:\s+)?([^\n。！？；]{6,120})',
        r'(?:完成|实现|达成|解决|学习|掌握|开发|创建|更新|设计|构建|优化|改进|修复|集成)(?:\s+)([^\n。！？；]{6,120})',
        # 英文目标模式
        r'(?:I want|I need|I plan|I intend)(?:\s+)([^\n.!?;]{6,120})',
        r'(?:goal is|task is|plan is)(?:\s+)?([^\n.!?;]{6,120})',
        r'(?:complete|implement|achieve|solve|learn|master|develop|create|update|design|build|optimize)(?:\s+)([^\n.!?;]{6,120})',
    ]
    
    goals = []
    seen = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            goal_text = match.group(1).strip()
            # 清理末尾标点
            goal_text = re.sub(r'[。！？；,，\.\?!;\-\|]$', '', goal_text)
            goal_text = goal_text.strip()
            
            if goal_text and goal_text not in seen and is_valid_goal(goal_text):
                goals.append(goal_text)
                seen.add(goal_text)
    
    return goals

def estimate_complexity(text: str) -> float:
    """估算目标复杂度"""
    complexity = 0.0
    keywords = {
        '复杂': 0.3, '困难': 0.3, '挑战': 0.2,
        '系统': 0.3, '架构': 0.3, '设计': 0.2,
        '集成': 0.2, '优化': 0.2, '重构': 0.3,
        '研究': 0.2, '分析': 0.2, '评估': 0.1,
        'multiple': 0.3, 'complex': 0.3, 'system': 0.3,
        'architecture': 0.3, 'design': 0.2, 'integration': 0.2,
        '项目': 0.2, '工程': 0.2, '平台': 0.2,
        '功能': 0.1, '模块': 0.1, '服务': 0.1
    }
    
    for keyword, score in keywords.items():
        if keyword.lower() in text.lower():
            complexity += score
    
    if len(text) > 80:
        complexity += 0.2
    
    return round(min(complexity, 1.0) * 10, 1)

def main():
    print("=" * 70)
    print("🎯 语义分析增强版目标提取算法")
    print("=" * 70)
    
    engine = create_engine('sqlite:///flow_ecosystem.db')
    SessionDB = sessionmaker(bind=engine)
    session = SessionDB()
    
    print("\n🔍 查询用户消息...")
    user_messages = session.query(Session).filter(
        Session.role == 'user',
        Session.content_text.isnot(None),
        Session.content_text != ''
    ).order_by(Session.timestamp.desc()).limit(100).all()
    
    print(f"找到 {len(user_messages)} 条用户消息")
    
    print("\n📝 提取目标（语义分析版）...")
    all_goals = []
    for msg in user_messages:
        goals = extract_goals_from_text(msg.content_text)
        for goal_text in goals:
            all_goals.append({
                'text': goal_text,
                'timestamp': msg.timestamp,
                'complexity': estimate_complexity(goal_text),
                'source_msg_id': msg.id
            })
    
    print(f"共提取到 {len(all_goals)} 个有效目标")
    
    if all_goals:
        print("\n📋 提取到的目标列表（按复杂度排序）:")
        sorted_goals = sorted(all_goals, key=lambda x: x['complexity'], reverse=True)
        
        for i, goal in enumerate(sorted_goals[:15], 1):
            print(f"\n{i}. [{goal['complexity']:.1f}] {goal['text']}")
            print(f"   来源: 消息ID {goal['source_msg_id']}")
            print(f"   时间: {goal['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        
        print("\n💾 保存目标到数据库...")
        saved_count = 0
        for goal in sorted_goals:
            existing = session.query(Goal).filter(
                Goal.declared_text.like(f'%{goal["text"][:30]}%')
            ).filter_by(status='active').first()
            
            if not existing:
                new_goal = Goal(
                    declared_text=goal['text'],
                    declared_at=goal['timestamp'],
                    status='active',
                    drift_score=0.0,
                    last_mentioned=datetime.now(),
                    complexity_score=goal['complexity']
                )
                session.add(new_goal)
                saved_count += 1
        
        session.commit()
        print(f"成功保存 {saved_count} 个新目标")
        
        total_goals = session.query(Goal).filter_by(status='active').count()
        print(f"\n📊 当前数据库中共有 {total_goals} 个活跃目标")
    else:
        print("\n⚠️ 未提取到有效目标")
        print("\n🔍 调试：显示前5条消息内容")
        for i, msg in enumerate(user_messages[:5], 1):
            print(f"\n消息 {i} (ID:{msg.id}):")
            preview = msg.content_text[:120]
            print(f"  {preview}...")
    
    session.close()
    print("\n✅ 完成！")

if __name__ == '__main__':
    main()
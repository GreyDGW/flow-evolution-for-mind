"""12-type core combination table matcher."""

from typing import List, Tuple, Dict

TYPE_COMBINATION_TABLE = [
    {"id": 1, "name": "完美型", "description": "五维全高，巅峰状态，产出与成长并进",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "high", "flow": "high", "cognitive": "high"}},
    {"id": 2, "name": "高效产出型", "description": "产出与心流俱佳，但认知进化停滞，需引入新挑战",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "high", "flow": "high", "cognitive": "low"}},
    {"id": 3, "name": "深度思考型", "description": "目标清晰、产出高、认知活跃，但心流状态不稳，易被打断",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "high", "flow": "low", "cognitive": "high"}},
    {"id": 4, "name": "战略清晰型", "description": "方向正确、状态好、成长快，但执行闭环薄弱，需强化落地",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "low", "flow": "high", "cognitive": "high"}},
    {"id": 5, "name": "盲目高效型", "description": "执行力强、状态好、成长快，但目标漂移，可能南辕北辙",
     "conditions": {"navigation": "high", "achievement": "low", "ewci": "high", "flow": "high", "cognitive": "high"}},
    {"id": 6, "name": "机械执行型", "description": "目标清晰、产出稳定，但无深度思考与心流，纯靠惯性驱动",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "high", "flow": "low", "cognitive": "low"}},
    {"id": 7, "name": "空想型", "description": "方向对、状态好，但产出低、认知停滞，想得多做得少",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "low", "flow": "high", "cognitive": "low"}},
    {"id": 8, "name": "低效忙碌型", "description": "心流好、产出多，但目标偏离且无认知成长，忙而无效",
     "conditions": {"navigation": "high", "achievement": "low", "ewci": "high", "flow": "high", "cognitive": "low"}},
    {"id": 9, "name": "探索型", "description": "目标清晰、认知活跃，但心流差、产出低，处于试错期",
     "conditions": {"navigation": "high", "achievement": "high", "ewci": "low", "flow": "low", "cognitive": "high"}},
    {"id": 10, "name": "游击型", "description": "产出高、认知快，但目标混乱、心流破碎，靠爆发力维持",
     "conditions": {"navigation": "high", "achievement": "low", "ewci": "high", "flow": "low", "cognitive": "high"}},
    {"id": 11, "name": "闭关型", "description": "心流与认知极佳，但目标失焦、产出为零，需重新对齐方向",
     "conditions": {"navigation": "high", "achievement": "low", "ewci": "low", "flow": "high", "cognitive": "high"}},
    {"id": 12, "name": "停滞型", "description": "五维全低，系统失效，需全面重启策略",
     "conditions": {"navigation": "low", "achievement": "low", "ewci": "low", "flow": "low", "cognitive": "low"}},
    {"id": 13, "name": "勤奋破坏型", "description": "危险：能力极强但方向错误，产出越多破坏越大",
     "conditions": {"navigation": "low", "achievement": "high", "ewci": "high", "flow": "high", "cognitive": "high"}},
]

THRESHOLD = 70
NAVIGATION_DANGER_THRESHOLD = 50


def classify_value(value: float, high_threshold: float = THRESHOLD) -> str:
    """Classify a value as 'high' or 'low'."""
    return "high" if value >= high_threshold else "low"


def match_type(
    navigation_percent: float,
    achievement_fit: float,
    ewci: float,
    flow_index: float,
    cognitive_evolution: float
) -> Dict:
    """
    Match the 12-type combination based on five dimensions.
    
    Special rule: Navigation < 50 (percent) forces '勤奋破坏型' or '停滞型'.
    """
    nav_high = navigation_percent >= NAVIGATION_DANGER_THRESHOLD
    
    if not nav_high:
        if all([
            achievement_fit >= THRESHOLD,
            ewci >= THRESHOLD,
            flow_index >= THRESHOLD,
            cognitive_evolution >= THRESHOLD
        ]):
            return TYPE_COMBINATION_TABLE[12]
        else:
            return TYPE_COMBINATION_TABLE[11]
    
    conditions = {
        "navigation": classify_value(navigation_percent),
        "achievement": classify_value(achievement_fit),
        "ewci": classify_value(ewci),
        "flow": classify_value(flow_index),
        "cognitive": classify_value(cognitive_evolution)
    }
    
    for entry in TYPE_COMBINATION_TABLE:
        if entry["conditions"] == conditions:
            return entry
    
    return TYPE_COMBINATION_TABLE[11]


class TypeMatcher:
    """类型匹配器"""
    
    def __init__(self):
        self.threshold = THRESHOLD
        self.navigation_danger_threshold = NAVIGATION_DANGER_THRESHOLD
    
    def match(self, navigation_percent: float, achievement_fit: float, ewci: float,
              flow_index: float, cognitive_evolution: float) -> Dict:
        """匹配类型"""
        return match_type(navigation_percent, achievement_fit, ewci, flow_index, cognitive_evolution)
    
    def classify_value(self, value: float) -> str:
        """分类值为高或低"""
        return classify_value(value, self.threshold)
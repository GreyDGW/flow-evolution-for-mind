import re
from typing import List, Dict


class IntentRecognizer:
    def __init__(self):
        self.intents = {
            "查询进度": ["进度", "状态", "怎么样了", "完成了吗"],
            "寻求建议": ["建议", "怎么办", "怎么做", "有什么好"],
            "记录问题": ["问题", "报错", "失败", "不行"],
            "分享进展": ["完成了", "搞定了", "解决了", "搞完了"],
            "请求帮助": ["帮忙", "帮帮我", "求助", "不会"],
        }
    
    def recognize(self, text: str) -> List[str]:
        matched = []
        text_lower = text.lower()
        
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched.append(intent)
                    break
        
        return matched if matched else ["其他"]
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        entities = {}
        
        project_match = re.search(r"(思维连续性保护器|多角色推理引擎|理财私域)", text)
        if project_match:
            entities["project"] = project_match.group(1)
        
        status_match = re.search(r"(完成|进行中|暂停|待定)", text)
        if status_match:
            entities["status"] = status_match.group(1)
        
        return entities
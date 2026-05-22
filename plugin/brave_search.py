import requests
from typing import List, Dict
import os


class BraveSearch:
    """Brave Search API 封装"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供 BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
    
    def search(self, query: str, count: int = 3) -> List[Dict]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": query,
            "count": count
        }
        
        # 修复：增加超时时间 + 重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                r = requests.get(self.base_url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()

                results = []
                for item in data.get("web", {}).get("results", [])[:count]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", "")[:100]
                    })
                return results

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"[BraveSearch] 超时，重试 {attempt + 1}/{max_retries}...")
                    continue
                print(f"[BraveSearch] 搜索超时（已重试{max_retries}次）")
                return []
            except requests.exceptions.RequestException as e:
                print(f"[BraveSearch] 搜索失败: {e}")
                return []
    
    def search_tools(self, label: str, evidence: str = "", count: int = 2) -> List[Dict]:
        query_map = {
            "执行卡壳": "how to overcome execution paralysis productivity tool",
            "目标漂移": "how to stay focused on goals productivity method",
            "心流不稳": "how to improve focus and concentration technique",
            "舒适区运转": "how to break out of comfort zone learning",
            "能量耗尽": "how to recover from burnout rest method",
            "产出饱和": "how to maintain productivity without burnout",
            "迷失探索": "how to find direction when lost exploration",
            "卡壳 burnout": "how to deal with burnout recovery",
            "四维协同": "how to maintain peak performance state",
            "高产出模式": "how to sustain high productivity",
            "认知突破": "how to apply new knowledge practice",
            "平稳推进": "productivity maintenance steady progress"
        }
        
        base_query = query_map.get(label, f"{label} productivity tool")
        if evidence:
            # 修复：evidence 包含 stuck_points，从20字扩到50字避免截断
            base_query += f" {evidence[:50]}"

        return self.search(base_query, count)
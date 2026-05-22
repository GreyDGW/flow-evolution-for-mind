"""
对话消息预处理器 - Turn Preprocessor

功能：
- 提取代码块（支持语言标注）并指纹化
- 提取引用块（>开头）并指纹化
- 提取长列表块（5+行，总长>200字）并指纹化
- 提取用户原创注释文本
- 清洗文本用于向量嵌入
"""

import re
import hashlib
from typing import Dict, List


class TurnPreprocessor:
    """单条对话消息预处理"""

    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)

    QUOTE_BLOCK_PATTERN = re.compile(r'>\s*[^\n]+')

    LIST_BLOCK_PATTERN = re.compile(r'(?:[-\*：]|\d+\.)\s+[^\n]+')

    MAX_EMBEDDING_LENGTH = 1000

    SNIPPET_HEAD_TAIL = 50

    LONG_QUOTE_THRESHOLD = 200

    def __init__(self):
        pass   

    def preprocess(self, content) -> Dict:
        """预处理单条消息"""
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = ' '.join(text_parts)
        elif isinstance(content, dict):
            content = content.get('text', '') if content.get('type') == 'text' else str(content)
        elif not isinstance(content, str):
            content = str(content) if content is not None else ''
        if not content:
            return self._empty_result()

        code_snippets = self._extract_code_blocks(content)
        quote_snippets = self._extract_quote_blocks(content)
        list_snippets = self._extract_long_lists(content)

        has_code = len(code_snippets) > 0
        code_hashes = [s['hash'] for s in code_snippets]
        quote_hashes = [s['hash'] for s in quote_snippets]
        list_hashes = [s['hash'] for s in list_snippets]

        user_notes = self._extract_user_notes(content, code_snippets, quote_snippets, list_snippets)

        embedding_text = self._build_embedding_text(user_notes, code_snippets, quote_snippets, list_snippets)

        return {
            "original": content,
            "embedding_text": embedding_text,
            "has_code": has_code,
            "code_hashes": code_hashes,
            "quote_hashes": quote_hashes,
            "list_hashes": list_hashes,
            "user_notes": user_notes
        }

    def _empty_result(self) -> Dict:
        return {
            "original": "",
            "embedding_text": "",
            "has_code": False,
            "code_hashes": [],
            "quote_hashes": [],
            "list_hashes": [],
            "user_notes": ""
        }

    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """提取代码块"""
        if not isinstance(content, str):
            return []
        blocks = []
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            code = match.group(2) if match.lastindex and match.group(2) else match.group(0)
            if code and len(code.strip()) > 0:
                block_hash = self._compute_hash(code.strip())
                snippet = self._extract_snippet(code.strip())
                blocks.append({
                    "hash": f"[CODE:{block_hash}]",
                    "snippet": snippet,
                    "start": match.start(),
                    "end": match.end()
                })
        return blocks   

    def _extract_quote_blocks(self, content: str) -> List[Dict]:
        """提取引用块"""
        blocks = []
        all_quotes = []
        for match in self.QUOTE_BLOCK_PATTERN.finditer(content):
            all_quotes.append(match.group(0))
        if all_quotes:
            combined = '\n'.join(all_quotes)
            if len(combined) >= self.LONG_QUOTE_THRESHOLD:
                block_hash = self._compute_hash(combined)
                snippet = self._extract_snippet(combined)
                blocks.append({
                    "hash": f"[QUOTE:{block_hash}]",
                    "snippet": snippet,
                    "start": content.find(all_quotes[0]) if all_quotes else 0,
                    "end": content.rfind(all_quotes[-1]) + len(all_quotes[-1]) if all_quotes else 0
                })
        return blocks

    def _extract_long_lists(self, content: str) -> List[Dict]:
        """提取长列表块（5+行，总长>200字）"""
        blocks = []
        all_items = []
        item_starts = []
        
        for match in self.LIST_BLOCK_PATTERN.finditer(content):
            all_items.append(match.group(0))
            item_starts.append(match.start())
        
        if len(all_items) >= 5:
            combined = ' '.join(all_items)
            if len(combined) >= self.LONG_QUOTE_THRESHOLD:
                block_hash = self._compute_hash(combined)
                snippet = self._extract_snippet(combined)
                blocks.append({
                    "hash": f"[LIST:{block_hash}]",
                    "snippet": snippet,
                    "start": item_starts[0] if item_starts else 0,
                    "end": match.end() + len(all_items[-1]) if item_starts else 0
                })
        return blocks

    def _compute_hash(self, text: str) -> str:
        """计算MD5哈希前8位"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

    def _extract_snippet(self, block_content: str) -> str:
        """提取块的头尾各SNIPPET_HEAD_TAIL字作为语义锚点"""
        if len(block_content) <= self.SNIPPET_HEAD_TAIL * 2:
            return block_content.strip()
        head = block_content[:self.SNIPPET_HEAD_TAIL]
        tail = block_content[-self.SNIPPET_HEAD_TAIL:]
        return f"{head}...{tail}"

    def _extract_user_notes(self, content: str, code_blocks: List, quote_blocks: List, list_blocks: List) -> str:
        """从原文切除所有块，得到用户原创注释"""
        all_blocks = sorted(
            code_blocks + quote_blocks + list_blocks,
            key=lambda x: x['start'],
            reverse=True
        )

        cleaned = content
        for block in all_blocks:
            cleaned = cleaned[:block['start']] + cleaned[block['end']:]

        lines = cleaned.split('\n')
        user_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                user_lines.append(line)

        return '\n'.join(user_lines).strip()

    def _build_embedding_text(self, user_notes: str, code_snippets: List, quote_snippets: List, list_snippets: List) -> str:
        """组装embedding_text（优先级：用户注释 > 引用块 > 列表块 > 代码块）"""
        parts = []

        if user_notes:
            user_priority = user_notes[:800]
            parts.append(user_priority)

        quote_text = ' '.join([s['snippet'] for s in quote_snippets])
        list_text = ' '.join([s['snippet'] for s in list_snippets])
        code_text = ' '.join([s['snippet'] for s in code_snippets])

        remaining = self.MAX_EMBEDDING_LENGTH - len(parts[0] if parts else '')

        if remaining > 0 and quote_text:
            parts.append(quote_text[:remaining])
            remaining -= len(quote_text)
        if remaining > 0 and list_text:
            parts.append(list_text[:remaining])
            remaining -= len(list_text)
        if remaining > 0 and code_text:
            parts.append(code_text[:remaining])

        embedding_text = ' '.join(parts)

        if len(embedding_text) > self.MAX_EMBEDDING_LENGTH:
            embedding_text = embedding_text[:self.MAX_EMBEDDING_LENGTH]

        return embedding_text.strip()


def preprocess_turn(content: str) -> Dict:
    """便捷函数：对单条消息进行预处理"""
    preprocessor = TurnPreprocessor()
    return preprocessor.preprocess(content)


if __name__ == "__main__":
    preprocessor = TurnPreprocessor()

    test_content = """
    我想优化这个查询性能，具体情况如下：

    > 这是之前的方案A，设计上存在一些缺陷需要调整
    > 之前的方案B，因为性能问题被废弃了
    > 重新设计的方案C，综合了A和B的优点
    > 新的方案D正在评审中，预计下周完成
    > 还有一些备选方案E和F需要进一步评估
    > 最终选定的方案G将综合所有优点

    优化计划包括以下步骤：
    - 第一步：深入分析慢查询的根本原因和性能瓶颈
    - 第二步：设计并添加合适的索引策略
    - 第三步：全面验证优化效果和性能提升
    - 第四步：持续监控关键性能指标
    - 第五步：详细的文档记录和知识沉淀
    - 第六步：团队分享和经验总结

    ```python
    def get_user_by_id(user_id):
        return db.query("SELECT * FROM users WHERE id = ?", user_id)
    ```

    帮我看看这个函数怎么优化。
    """

    result = preprocessor.preprocess(test_content)

    print("=" * 60)
    print("预处理器测试")
    print("=" * 60)
    print(f"\n原文长度: {len(result['original'])} 字")
    print(f"用户注释: {len(result['user_notes'])} 字")
    print(f"清洗后文本: {len(result['embedding_text'])} 字")
    print(f"包含代码: {result['has_code']}")
    print(f"代码块哈希: {result['code_hashes']}")
    print(f"引用块哈希: {result['quote_hashes']}")
    print(f"列表块哈希: {result['list_hashes']}")
    print(f"\n用户注释预览:\n{result['user_notes'][:200]}")
    print(f"\n清洗后文本预览:\n{result['embedding_text'][:200]}")
    print("=" * 60)

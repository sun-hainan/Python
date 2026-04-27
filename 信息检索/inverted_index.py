# -*- coding: utf-8 -*-
"""
算法实现：信息检索 / inverted_index

本文件实现 inverted_index 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict


class InvertedIndex:
    """倒排索引"""

    def __init__(self):
        self.index = {}  # word -> [(doc_id, freq, positions), ...]
        self.doc_count = 0
        self.doc_lengths = {}

    def add_document(self, doc_id: int, tokens: List[str]):
        """
        添加文档到索引

        参数：
            doc_id: 文档ID
            tokens: 分词后的词列表
        """
        term_freq = defaultdict(int)
        positions = defaultdict(list)

        for pos, token in enumerate(tokens):
            term_freq[token] += 1
            positions[token].append(pos)

        self.doc_lengths[doc_id] = len(tokens)

        for word, freq in term_freq.items():
            if word not in self.index:
                self.index[word] = []

            self.index[word].append({
                'doc_id': doc_id,
                'freq': freq,
                'positions': positions[word]
            })

        self.doc_count += 1

    def search(self, query: List[str], method: str = 'AND') -> List[int]:
        """
        搜索包含查询词的文档

        参数：
            query: 查询词列表
            method: 'AND' 或 'OR'

        返回：匹配的文档ID列表
        """
        if not query:
            return []

        # 获取每个词的文档列表
        posting_lists = []
        for word in query:
            if word in self.index:
                posting_lists.append(set(item['doc_id'] for item in self.index[word]))

        if not posting_lists:
            return []

        if method == 'AND':
            # 交集
            result = posting_lists[0]
            for pl in posting_lists[1:]:
                result &= pl
            return list(result)

        elif method == 'OR':
            # 并集
            result = set()
            for pl in posting_lists:
                result |= pl
            return list(result)

        return []

    def get_term_info(self, term: str) -> Dict:
        """获取词项信息"""
        if term not in self.index:
            return {'df': 0, 'postings': []}

        postings = self.index[term]
        return {
            'df': len(postings),  # 文档频率
            'postings': postings
        }


def simple_tokenize(text: str) -> List[str]:
    """简单分词"""
    # 去除标点，转小写，按空格分割
    for punct in '.,!?;:"\'()-':
        text = text.replace(punct, ' ')
    return text.lower().split()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 倒排索引测试 ===\n")

    # 示例文档
    docs = {
        1: "Python is a great programming language",
        2: "Java is also popular for enterprise",
        3: "Python and Java both support OOP",
        4: "Machine learning uses Python extensively",
        5: "Deep learning is part of AI",
    }

    # 构建索引
    index = InvertedIndex()
    for doc_id, text in docs.items():
        tokens = simple_tokenize(text)
        index.add_document(doc_id, tokens)
        print(f"文档{doc_id}: {text}")
        print(f"  分词: {tokens}")

    print()

    # 搜索
    queries = [
        ["python"],
        ["python", "java"],
        ["machine", "learning"],
        ["python", "enterprise"],
    ]

    for query in queries:
        results = index.search(query, method='AND')
        print(f"AND搜索 {query}: 文档 {results}")

    print()

    # 词项信息
    for word in ["python", "java", "programming"]:
        info = index.get_term_info(word)
        print(f"'{word}': df={info['df']}")

    print("\n说明：")
    print("  - 倒排索引是搜索引擎的核心")
    print("  - 支持AND/OR/NOT等布尔查询")
    print("  - 可以扩展支持TF-IDF、BM25等排序")

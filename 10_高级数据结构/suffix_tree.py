"""
Suffix Tree（后缀树）
==========================================

【原理】
包含字符串所有后缀的压缩Trie。
O(n)构建，用于子串匹配等问题。

【时间复杂度】
- 构建: O(n)
- 查询: O(m)

【应用场景】
- 子串匹配
- 最长重复子串
- 数据压缩
"""

from typing import Optional


class SuffixTreeNode:
    def __init__(self):
        self.children = {}
        self.label = ""


class SuffixTree:
    """后缀树（简化版）"""

    def __init__(self, s):
        self.s = s
        self.root = SuffixTreeNode()
        self._build()

    def _build(self):
        """构建后缀树"""
        s = self.s
        for i in range(len(s)):
            current = self.root
            for j in range(i, len(s)):
                char = s[j]
                if char not in current.children:
                    current.children[char] = SuffixTreeNode()
                current = current.children[char]

    def search(self, pattern):
        """搜索子串"""
        current = self.root
        for char in pattern:
            if char not in current.children:
                return False
            current = current.children[char]
        return True


if __name__ == "__main__":
    print("Suffix Tree测试")
    tree = SuffixTree("banana")
    print(f"搜索'nan': {tree.search('nan')}")
    print(f"搜索'xxx': {tree.search('xxx')}")

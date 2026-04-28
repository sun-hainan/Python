"""
Radix Tree（基数树）
==========================================

【算法原理】
压缩前缀树，共享最长公共前缀的路径。
比Trie更节省空间，适合IP路由和字符串索引。

【时间复杂度】
- 插入: O(k) k为键长
- 查找: O(k)
- 空间: O(total_length)

【应用场景】
- IP路由（最长前缀匹配）
- 文件系统路径
- 内存管理
"""

from typing import Optional


class RadixNode:
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.children = {}
        self.value = None


class RadixTree:
    """基数树/压缩前缀树"""

    def __init__(self):
        self.root = RadixNode()

    def insert(self, key: str, value) -> None:
        """插入键值对"""
        node = self.root
        while key:
            # 找到第一个匹配的前缀
            for child_key in node.children:
                common = self._common_prefix(key, child_key)
                if common:
                    if common == child_key:
                        # 完全匹配子节点前缀
                        node = node.children[child_key]
                        key = key[common:]
                        break
                    else:
                        # 需要分裂节点
                        new_node = RadixNode(child_key[common:])
                        new_node.children = node.children.pop(child_key)
                        node.children[common] = new_node
                        node = new_node
                        key = key[common:]
                        break
            else:
                # 没有匹配，创建新子节点
                node.children[key] = RadixNode("")
                node.children[key].value = value
                return

        node.value = value

    def search(self, key: str) -> Optional:
        """查找"""
        node = self.root
        while key:
            if key in node.children:
                node = node.children[key]
                key = ""
            elif any(key.startswith(cp) for cp in node.children):
                for cp in node.children:
                    if key.startswith(cp):
                        node = node.children[cp]
                        key = key[len(cp):]
                        break
            else:
                return None
        return node.value if node else None

    def longest_prefix(self, key: str) -> Optional:
        """最长前缀匹配"""
        node = self.root
        match = ""
        while key:
            if key in node.children:
                match += key
                return match, node.children[key].value
            for cp in node.children:
                if key.startswith(cp):
                    match += cp
                    node = node.children[cp]
                    key = key[len(cp):]
                    break
            else:
                return match if match else None
        return match, node.value if node else None

    def _common_prefix(self, s1, s2):
        """计算公共前缀"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return s1[:i]


if __name__ == "__main__":
    print("Radix Tree测试")
    tree = RadixTree()
    tree.insert("apple", 1)
    tree.insert("app", 2)
    tree.insert("application", 3)
    print(f"search('app'): {tree.search('app')}")
    print(f"longest_prefix('appl'): {tree.longest_prefix('appl')}")

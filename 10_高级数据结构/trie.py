"""
Trie（字典树）
==========================================

【算法原理】
每个节点代表一个字符，从根到某节点的路径表示一个前缀。
利用字符串的公共前缀来高效存储和检索。

【时间复杂度】
- 插入: O(m)，m为字符串长度
- 搜索: O(m)
- 前缀匹配: O(m)

【空间复杂度】O(m × n)，n为字符串数，m为平均长度

【应用场景】
- 自动补全
- IP路由（最长前缀匹配）
- 打字预测
- 词典检索
"""

from typing import Optional, List


class TrieNode:
    """Trie树节点"""
    def __init__(self):
        # 子节点映射：字符 -> TrieNode
        self.children = {}
        # 是否为单词结尾
        self.is_end = False
        # 词频（可选，用于优先级排序）
        self.freq = 0


class Trie:
    """
    字典树/前缀树

    【核心操作】
    - insert(word): 插入字符串
    - search(word): 精确查找
    - starts_with(prefix): 前缀匹配
    - autocomplete(prefix): 自动补全
    """

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, freq: int = 1) -> None:
        """
        插入字符串

        【步骤】
        1. 从根节点开始
        2. 对每个字符，若子节点存在则沿用，否则创建
        3. 最后一个节点标记为单词结尾
        """
        node = self.root
        for char in word:
            # 如果子节点不存在，则创建
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        # 标记为单词结尾
        node.is_end = True
        node.freq += freq

    def search(self, word: str) -> bool:
        """
        精确查找字符串
        """
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """
        判断是否存在以prefix为前缀的字符串
        """
        return self._find_node(prefix) is not None

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """查找prefix对应的节点，不考虑is_end"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def autocomplete(self, prefix: str, max_results: int = 5) -> List[str]:
        """
        自动补全：返回以prefix开头的所有字符串

        【实现】从prefix节点开始DFS收集所有完整单词
        """
        node = self._find_node(prefix)
        if node is None:
            return []

        results = []
        self._dfs_collect(node, prefix, results, max_results)
        # 按词频排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [word for word, freq in results]

    def _dfs_collect(self, node: TrieNode, path: str,
                   results: List[tuple], max_results: int) -> None:
        """DFS收集所有完整路径"""
        if len(results) >= max_results:
            return

        # 如果是单词结尾，记录
        if node.is_end:
            results.append((path, node.freq))

        # 递归遍历子节点
        for char, child in node.children.items():
            self._dfs_collect(child, path + char, results, max_results)

    def prefix_count(self, prefix: str) -> int:
        """统计以prefix为前缀的字符串数量"""
        node = self._find_node(prefix)
        if node is None:
            return 0
        count = [0]
        self._dfs_count(node, count)
        return count[0]

    def _dfs_count(self, node: TrieNode, count: List[int]) -> None:
        """DFS计数"""
        if node.is_end:
            count[0] += 1
        for child in node.children.values():
            self._dfs_count(child, count)

    def longest_common_prefix(self) -> str:
        """
        找出所有字符串的最长公共前缀

        【方法】从根开始DFS，每次只沿唯一的子节点前进
        """
        if self.root.is_end:
            return ""

        prefix = []
        node = self.root

        while len(node.children) == 1 and not node.is_end:
            # 只有一个子节点
            char, next_node = next(iter(node.children.items()))
            prefix.append(char)
            node = next_node

        return ''.join(prefix)

    def delete(self, word: str) -> bool:
        """
        删除字符串

        【策略】如果删除后节点无子节点且非其他词前缀，则剪枝
        """
        # 先判断存在
        if not self.search(word):
            return False

        # DFS删除，stack存(node, char)
        stack = [(self.root, None)]
        for char in word:
            stack.append((stack[-1][0].children[char], char))

        # 找到末尾节点
        end_node = stack[-1][0]
        end_node.is_end = False

        # 剪枝：从叶子向根
        for i in range(len(stack) - 1, 0, -1):
            node, char = stack[i]
            parent, _ = stack[i - 1]
            if not node.children and not node.is_end:
                del parent.children[char]
            else:
                break

        return True


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Trie字典树 - 测试")
    print("=" * 50)

    trie = Trie()

    # 插入词汇
    words = ["apple", "app", "application", "apply", "apt",
             "banana", "band", "bandana",
             "cat", "car", "card", "care"]
    for w in words:
        trie.insert(w)

    # 测试精确查找
    print("\n【测试】精确查找")
    for w in ["apple", "app", "apricot", "banana"]:
        print(f"  '{w}': {trie.search(w)}")

    # 测试前缀匹配
    print("\n【测试】前缀匹配")
    for p in ["app", "ban", "ca", "xyz"]:
        print(f"  starts_with('{p}'): {trie.starts_with(p)}")

    # 测试自动补全
    print("\n【测试】自动补全 'ap'")
    results = trie.autocomplete("ap", max_results=5)
    print(f"  结果: {results}")

    # 测试前缀计数
    print("\n【测试】前缀计数")
    for p in ["ap", "ba", "car"]:
        print(f"  '{p}': {trie.prefix_count(p)} 个")

    # 测试最长公共前缀
    print("\n【测试】最长公共前缀")
    print(f"  所有词的最长公共前缀: '{trie.longest_common_prefix()}'")

    # 测试删除
    print("\n【测试】删除 'app'")
    trie.delete("app")
    print(f"  search('app'): {trie.search('app')}")
    print(f"  search('apple'): {trie.search('apple')}")

    # 验证树结构
    print("\n【测试】树结构验证")
    print(f"  根节点子节点数: {len(trie.root.children)}")
    print(f"  'a'开头的词: {trie.autocomplete('a', 10)}")

    print("\n" + "=" * 50)
    print("Trie字典树测试完成！")
    print("=" * 50)

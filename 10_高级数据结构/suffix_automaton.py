"""
Suffix Automaton（后缀自动机）
==========================================

【算法原理】
后缀自动机是一个识别字符串所有后缀的确定有限自动机（DFA）。
能以 O(n) 的时间构建，支持 O(1) 的后缀查询。

【时间复杂度】
- 构建: O(n)
- 查询: O(1) per character

【空间复杂度】O(2n - 1) 个状态

【应用场景】
- 字符串匹配
- 最长重复子串
- 不同子串计数
- 最短唯一子串
- 多个字符串的公共子串
"""

from typing import List, Optional, Dict


class SAMState:
    """后缀自动机状态"""
    def __init__(self):
        # 转移函数：字符 -> 状态
        self.next = {}
        # 最长字符串长度
        self.len = 0
        # 通过后缀链接指向的状态（父状态）
        self.link = -1
        # 该状态表示的endpos等价类的大小（出现次数）
        self.count = 0


class SuffixAutomaton:
    """
    后缀自动机

    【核心概念】
    - 每个状态表示一些结束位置相同的字符串集合
    - st[i].len: 该状态能表示的最长字符串长度
    - st[i].link: 父状态（表示当前状态表示的串的缩短版）
    - st[i].next: 转移
    """

    def __init__(self, s: str = ""):
        self.s = s
        self.n = len(s)
        self.states = []
        self.last = 0  # 最近添加的状态

        # 初始化：根状态
        self._sam_init()
        if s:
            self._build(s)

    def _sam_init(self) -> None:
        """初始化：创建根状态"""
        self.states.append(SAMState())
        self.states[0].len = 0
        self.states[0].link = -1

    def _build(self, s: str) -> None:
        """
        构建后缀自动机

        【方法】增量构建，每次添加一个字符

        【对于每个新字符c】
        1. 创建新状态cur，len = st[last].len + 1
        2. 从last开始找能接受c的状态p
        3. 如果p的转移c存在...
        4. 如果不存在，创建转移
        """
        for c in s:
            self._sam_extend(c)

    def _sam_extend(self, c: str) -> None:
        """
        增量添加字符c

        【步骤】
        1. 创建新状态 cur（len = states[last].len + 1）
        2. 从last开始，如果转移c不存在，添加转移
        3. 如果某个状态p已经有转移c：
           - 设 q = states[p].next[c]
           - 如果 states[p].len + 1 == states[q].len，直接链接
           - 否则需要克隆状态
        """
        # 第1步：创建新状态
        cur = len(self.states)
        self.states.append(SAMState())
        self.states[cur].len = self.states[self.last].len + 1
        self.states[cur].count = 1  # 新状态出现1次

        # 第2步：添加转移
        p = self.last
        while p != -1 and c not in self.states[p].next:
            self.states[p].next[c] = cur
            p = self.states[p].link

        if p == -1:
            # 如果到达根状态还没找到，设置link为0
            self.states[cur].link = 0
        else:
            # 找到了某个状态p有转移c
            q = self.states[p].next[c]

            # 检查是否需要克隆
            if self.states[p].len + 1 == self.states[q].len:
                self.states[cur].link = q
            else:
                # 需要克隆状态q
                clone = len(self.states)
                self.states.append(SAMState())
                self.states[clone].len = self.states[p].len + 1
                self.states[clone].next = self.states[q].next.copy()
                self.states[clone].link = self.states[q].link
                self.states[clone].count = 0  # 克隆状态不计入出现次数

                # 修改q的link
                while p != -1 and self.states[p].next.get(c) == q:
                    self.states[p].next[c] = clone
                    p = self.states[p].link

                self.states[q].link = self.states[cur].link = clone

        self.last = cur

    def count_occurrences(self) -> None:
        """计算每个状态的出现次数（按len降序）"""
        # 按len降序排序状态
        order = sorted(range(len(self.states)),
                      key=lambda x: self.states[x].len, reverse=True)

        # 沿后缀链接传播count
        for v in order:
            if self.states[v].link != -1:
                self.states[self.states[v].link].count += self.states[v].count

    def contains(self, pattern: str) -> bool:
        """判断模式串是否在文本中"""
        v = 0  # 从根状态开始
        for c in pattern:
            if c not in self.states[v].next:
                return False
            v = self.states[v].next[c]
        return True

    def find_longest_common_substring(self, t: str) -> tuple:
        """
        找与t的最长公共子串

        【返回】(长度, 子串)
        """
        v = 0
        longest_len = 0
        longest_pos = 0
        cur_len = 0

        for i, c in enumerate(t):
            # 尝试沿转移走
            while v != -1 and c not in self.states[v].next:
                v = self.states[v].link
                if v != -1:
                    cur_len = self.states[v].len

            if v == -1:
                v = 0
                cur_len = 0
            else:
                v = self.states[v].next[c]
                cur_len += 1

                if cur_len > longest_len:
                    longest_len = cur_len
                    longest_pos = i - cur_len + 1

        return longest_len, t[longest_pos:longest_pos + longest_len]

    def count_distinct_substrings(self) -> int:
        """
        统计不同子串数量

        【公式】sum(len(v) - len(link(v))) for all v
        """
        total = 0
        for v in range(1, len(self.states)):  # 跳过根状态
            total += self.states[v].len - self.states[self.states[v].link].len
        return total

    def get_all_substrings(self, pattern: str) -> List[str]:
        """
        获取所有与SAM中某模式匹配的子串（用于调试）
        """
        results = []
        v = 0
        current = ""

        for c in pattern:
            if c in self.states[v].next:
                current += c
                v = self.states[v].next[c]
                results.append(current)
            else:
                break

        return results

    def display_states(self) -> None:
        """打印所有状态（调试用）"""
        print("\n【后缀自动机状态】")
        print(f"{'id':>3} {'len':>4} {'link':>4} {'next':>20} {'count':>6}")
        print("-" * 50)
        for i, st in enumerate(self.states):
            next_str = str(dict(st.next)) if st.next else "{}"
            print(f"{i:>3} {st.len:>4} {st.link:>4} {next_str:>20} {st.count:>6}")


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Suffix Automaton（后缀自动机） - 测试")
    print("=" * 50)

    # 测试1：基本构建
    print("\n【测试1】构建后缀自动机")
    s = "ababa"
    sam = SuffixAutomaton(s)
    print(f"  字符串: '{s}'")
    print(f"  状态数: {len(sam.states)}")
    sam.display_states()

    # 测试2：子串包含判断
    print("\n【测试2】子串包含判断")
    test_patterns = ["aba", "bab", "abc", "a", "ababa"]
    for p in test_patterns:
        print(f"  contains('{p}'): {sam.contains(p)}")

    # 测试3：不同子串计数
    print("\n【测试3】不同子串计数")
    distinct = sam.count_distinct_substrings()
    print(f"  '{s}' 的不同子串数: {distinct}")
    print(f"  理论值: {len(s) * (len(s) + 1) // 2} (所有子串)")

    # 测试4：出现次数
    print("\n【测试4】子串出现次数")
    sam.count_occurrences()
    print(f"  状态出现次数已计算")
    for i, st in enumerate(sam.states):
        if st.count > 0:
            print(f"  状态{i}: count={st.count}")

    # 测试5：最长公共子串
    print("\n【测试5】与另一字符串的最长公共子串")
    t = "baba"
    length, substring = sam.find_longest_common_substring(t)
    print(f"  SAM='{s}', T='{t}'")
    print(f"  最长公共子串: '{substring}' (长度={length})")

    # 测试6：更复杂的例子
    print("\n【测试6】复杂字符串")
    s2 = "aabbabacaba"
    sam2 = SuffixAutomaton(s2)
    print(f"  字符串: '{s2}'")
    print(f"  状态数: {len(sam2.states)}")
    print(f"  不同子串数: {sam2.count_distinct_substrings()}")

    t2 = "abacab"
    length2, substring2 = sam2.find_longest_common_substring(t2)
    print(f"  与'{t2}'的最长公共子串: '{substring2}' (长度={length2})")

    print("\n" + "=" * 50)
    print("后缀自动机测试完成！")
    print("=" * 50)

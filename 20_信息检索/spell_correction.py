# -*- coding: utf-8 -*-

"""

算法实现：信息检索 / spell_correction



本文件实现 spell_correction 相关的算法功能。

"""



from typing import List, Tuple, Dict, Set





def edit_distance(s1: str, s2: str) -> int:

    """

    计算编辑距离（Levenshtein Distance）



    参数：

        s1: 字符串1

        s2: 字符串2



    返回：编辑距离

    """

    m, n = len(s1), len(s2)



    # dp[i][j] = s1[0:i] 和 s2[0:j] 的编辑距离

    dp = [[0] * (n + 1) for _ in range(m + 1)]



    for i in range(m + 1):

        dp[i][0] = i  # 删除操作

    for j in range(n + 1):

        dp[0][j] = j  # 插入操作



    for i in range(1, m + 1):

        for j in range(1, n + 1):

            if s1[i-1] == s2[j-1]:

                dp[i][j] = dp[i-1][j-1]

            else:

                dp[i][j] = 1 + min(

                    dp[i-1][j],    # 删除

                    dp[i][j-1],    # 插入

                    dp[i-1][j-1]   # 替换

                )



    return dp[m][n]





def edits(word: str) -> Set[str]:

    """

    生成编辑距离为1的所有可能字符串



    用于生成候选纠正词

    """

    results = set()



    # 删除

    for i in range(len(word)):

        results.add(word[:i] + word[i+1:])



    # 插入

    for i in range(len(word) + 1):

        for c in 'abcdefghijklmnopqrstuvwxyz':

            results.add(word[:i] + c + word[i:])



    # 替换

    for i in range(len(word)):

        for c in 'abcdefghijklmnopqrstuvwxyz':

            if c != word[i]:

                results.add(word[:i] + c + word[i+1:])



    # 换位

    for i in range(len(word) - 1):

        results.add(word[:i] + word[i+1] + word[i] + word[i+2:])



    return results





class SpellChecker:

    """拼写检查器"""



    def __init__(self, vocabulary: Set[str]):

        """

        参数：

            vocabulary: 正确拼写的词集合

        """

        self.vocab = vocabulary

        self.word_freq = {}



    def candidates(self, word: str) -> List[Tuple[str, int]]:

        """

        找出可能的纠正词



        返回：[(候选词, 编辑距离), ...]

        """

        word = word.lower()



        # 1. 词本身在词典中

        if word in self.vocab:

            return [(word, 0)]



        # 2. 编辑距离为1的词

        edits1 = edits(word)

        cand1 = [(w, 1) for w in edits1 if w in self.vocab]



        # 3. 编辑距离为2的词（如果1没有找到）

        if not cand1:

            cand2 = []

            for e1 in edits1:

                for e2 in edits(e1):

                    if e2 in self.vocab:

                        cand2.append((e2, 2))

            return cand2



        return cand1



    def correct(self, word: str) -> str:

        """返回最可能的纠正"""

        candidates = self.candidates(word)

        if not candidates:

            return word



        # 如果有编辑距离0的直接返回

        for word_cand, dist in candidates:

            if dist == 0:

                return word_cand



        # 否则返回编辑距离最小的

        min_dist = min(dist for _, dist in candidates)

        for word_cand, dist in candidates:

            if dist == min_dist:

                return word_cand



        return word





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 拼写纠正测试 ===\n")



    # 词典

    vocab = {"algorithm", "computer", "programming", "python", "java",

             "data", "structure", "algorithm", "correct", "spelling"}



    checker = SpellChecker(vocab)



    # 测试

    misspellings = ["algorthm", "progarmming", "pythno", "algo", "strcuture"]



    print("拼写纠正：")

    for word in misspellings:

        corrected = checker.correct(word)

        candidates = checker.candidates(word)

        print(f"  {word} -> {corrected} (候选: {candidates})")



    # 编辑距离

    print("\n编辑距离示例：")

    pairs = [("algorithm", "algorthm"), ("kitten", "sitting")]

    for s1, s2 in pairs:

        dist = edit_distance(s1, s2)

        print(f"  edit_distance('{s1}', '{s2}') = {dist}")



    print("\n说明：")

    print("  - 编辑距离是最基础的拼写纠正方法")

    print("  - 实际系统会用语言模型选择最佳纠正")

    print("  - Google's Spelling Suggestions使用统计翻译模型")


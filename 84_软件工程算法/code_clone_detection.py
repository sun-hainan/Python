# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / code_clone_detection



本文件实现 code_clone_detection 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

from collections import Counter

import re





class CodeSnippet:

    """

    代码片段类

    """

    

    def __init__(self, file_path: str, start_line: int, 

                 end_line: int, content: str):

        self.file_path = file_path

        self.start_line = start_line

        self.end_line = end_line

        self.content = content

        self.tokens: List[str] = []

        self.metrics: Dict[str, float] = {}

    

    def tokenize(self):

        """将代码转换为token序列"""

        # 简单token化

        pattern = r'\b\w+\b|[+\-*/=<>!&|]+|[{}();,]'

        self.tokens = re.findall(pattern, self.content.lower())

    

    def compute_metrics(self):

        """计算代码度量"""

        lines = self.content.split('\n')

        

        # 物理行数

        self.metrics['lines'] = len(lines)

        

        # 字符数

        self.metrics['chars'] = len(self.content)

        

        # 注释行数

        self.metrics['comment_lines'] = sum(

            1 for line in lines 

            if re.match(r'\s*//', line) or re.match(r'\s*#', line)

        )

        

        # 空白字符数

        self.metrics['whitespace'] = sum(

            len(re.findall(r'\s', line)) for line in lines

        )

        

        # 独特字符数

        self.metrics['unique_chars'] = len(set(self.content))

        

        # 函数调用数

        self.metrics['function_calls'] = len(re.findall(r'\w+\(', self.content))





class CodeCloneDetector:

    """

    代码克隆检测器

    """

    

    def __init__(self, similarity_threshold: float = 0.7):

        """

        初始化

        

        参数:

            similarity_threshold: 相似度阈值

        """

        self.threshold = similarity_threshold

        self.snippets: List[CodeSnippet] = []

    

    def add_snippet(self, snippet: CodeSnippet):

        """

        添加代码片段

        

        参数:

            snippet: 代码片段

        """

        snippet.tokenize()

        snippet.compute_metrics()

        self.snippets.append(snippet)

    

    def text_similarity(self, s1: str, s2: str) -> float:

        """

        计算文本相似度（简单行级比较）

        

        参数:

            s1: 文本1

            s2: 文本2

        

        返回:

            相似度 (0-1)

        """

        lines1 = set(s1.split('\n'))

        lines2 = set(s2.split('\n'))

        

        intersection = len(lines1 & lines2)

        union = len(lines1 | lines2)

        

        if union == 0:

            return 1.0

        

        return intersection / union

    

    def token_similarity(self, snippet1: CodeSnippet, 

                        snippet2: CodeSnippet) -> float:

        """

        计算token级相似度

        

        参数:

            snippet1: 片段1

            snippet2: 片段2

        

        返回:

            相似度 (0-1)

        """

        tokens1 = Counter(snippet1.tokens)

        tokens2 = Counter(snippet2.tokens)

        

        # Jaccard相似度

        common_tokens = sum((tokens1 & tokens2).values())

        total_tokens = sum((tokens1 | tokens2).values())

        

        if total_tokens == 0:

            return 0.0

        

        return common_tokens / total_tokens

    

    def metric_similarity(self, snippet1: CodeSnippet,

                        snippet2: CodeSnippet) -> float:

        """

        基于度量的相似度

        

        参数:

            snippet1: 片段1

            snippet2: 片段2

        

        返回:

            相似度 (0-1)

        """

        if not snippet1.metrics or not snippet2.metrics:

            return 0.0

        

        total_diff = 0.0

        count = 0

        

        for key in snippet1.metrics:

            if key in snippet2.metrics:

                v1 = snippet1.metrics[key]

                v2 = snippet2.metrics[key]

                

                if v1 + v2 > 0:

                    diff = abs(v1 - v2) / max(v1, v2)

                    total_diff += (1.0 - diff)

                    count += 1

        

        if count == 0:

            return 0.0

        

        return total_diff / count

    

    def combined_similarity(self, snippet1: CodeSnippet,

                          snippet2: CodeSnippet) -> float:

        """

        综合相似度

        

        参数:

            snippet1: 片段1

            snippet2: 片段2

        

        返回:

            综合相似度

        """

        text_sim = self.text_similarity(snippet1.content, snippet2.content)

        token_sim = self.token_similarity(snippet1, snippet2)

        metric_sim = self.metric_similarity(snippet1, snippet2)

        

        # 加权平均

        return 0.4 * text_sim + 0.4 * token_sim + 0.2 * metric_sim

    

    def find_clones(self) -> List[Tuple[int, int, float]]:

        """

        查找代码克隆

        

        返回:

            [(片段1索引, 片段2索引, 相似度), ...]

        """

        clones = []

        n = len(self.snippets)

        

        for i in range(n):

            for j in range(i + 1, n):

                similarity = self.combined_similarity(

                    self.snippets[i], 

                    self.snippets[j]

                )

                

                if similarity >= self.threshold:

                    clones.append((i, j, similarity))

        

        return clones





def simple_clone_detection(code1: str, code2: str) -> Dict:

    """

    简单的克隆检测（不使用类）

    

    参数:

        code1: 代码1

        code2: 代码2

    

    返回:

        检测结果

    """

    # 行级比较

    lines1 = set(code1.split('\n'))

    lines2 = set(code2.split('\n'))

    

    intersection = len(lines1 & lines2)

    union = len(lines1 | lines2)

    

    line_similarity = intersection / union if union > 0 else 1.0

    

    # 字符级比较

    len1 = len(code1)

    len2 = len(code2)

    char_similarity = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

    

    return {

        'line_similarity': line_similarity,

        'char_similarity': char_similarity,

        'likely_clone': line_similarity > 0.5 and char_similarity > 0.3

    }





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本克隆检测

    print("=" * 50)

    print("测试1: 基本代码克隆检测")

    print("=" * 50)

    

    code1 = """

function add(a, b) {

    return a + b;

}

"""

    

    code2 = """

function add(x, y) {

    return x + y;

}

"""

    

    code3 = """

function multiply(a, b) {

    return a * b;

}

"""

    

    result1 = simple_clone_detection(code1, code2)

    result2 = simple_clone_detection(code1, code3)

    

    print("代码1 vs 代码2 (相似函数):")

    print(f"  行相似度: {result1['line_similarity']:.4f}")

    print(f"  字符相似度: {result1['char_similarity']:.4f}")

    print(f"  可能是克隆: {result1['likely_clone']}")

    

    print("\n代码1 vs 代码3 (不同函数):")

    print(f"  行相似度: {result2['line_similarity']:.4f}")

    print(f"  字符相似度: {result2['char_similarity']:.4f}")

    print(f"  可能是克隆: {result2['likely_clone']}")

    

    # 测试用例2：代码片段处理

    print("\n" + "=" * 50)

    print("测试2: 代码片段处理")

    print("=" * 50)

    

    snippet1 = CodeSnippet("file1.py", 1, 5, code1)

    snippet2 = CodeSnippet("file2.py", 10, 14, code2)

    

    snippet1.tokenize()

    snippet1.compute_metrics()

    

    print(f"片段1 tokens: {snippet1.tokens}")

    print(f"片段1 度量: {snippet1.metrics}")

    

    # 测试用例3：完整克隆检测

    print("\n" + "=" * 50)

    print("测试3: 完整克隆检测流程")

    print("=" * 50)

    

    detector = CodeCloneDetector(similarity_threshold=0.5)

    

    snippets = [

        CodeSnippet("util1.py", 1, 5, "def add(a, b):\n    return a + b\n"),

        CodeSnippet("util2.py", 10, 14, "def add(x, y):\n    return x + y\n"),

        CodeSnippet("math1.py", 20, 25, "def multiply(a, b):\n    return a * b\n"),

        CodeSnippet("math2.py", 30, 35, "def multiply(x, y):\n    return x * y\n"),

        CodeSnippet("calc.py", 40, 45, "def divide(a, b):\n    return a / b\n"),

    ]

    

    for s in snippets:

        detector.add_snippet(s)

    

    clones = detector.find_clones()

    

    print(f"检测到的克隆对数: {len(clones)}")

    for i, j, sim in clones:

        print(f"  {detector.snippets[i].file_path} <-> "

              f"{detector.snippets[j].file_path}: {sim:.4f}")

    

    # 测试用例4：Token级相似度

    print("\n" + "=" * 50)

    print("测试4: Token级相似度")

    print("=" * 50)

    

    snippet1 = CodeSnippet("a.py", 1, 3, "x = a + b\ny = c + d\n")

    snippet2 = CodeSnippet("b.py", 1, 3, "p = x + y\nq = m + n\n")

    

    snippet1.tokenize()

    snippet2.tokenize()

    

    detector = CodeCloneDetector()

    sim = detector.token_similarity(snippet1, snippet2)

    

    print(f"片段1 tokens: {snippet1.tokens}")

    print(f"片段2 tokens: {snippet2.tokens}")

    print(f"Token相似度: {sim:.4f}")

    

    # 测试用例5：度量相似度

    print("\n" + "=" * 50)

    print("测试5: 度量级相似度")

    print("=" * 50)

    

    snippet1 = CodeSnippet("file1.py", 1, 5, "x = 1\ny = 2\nz = 3\n")

    snippet2 = CodeSnippet("file2.py", 1, 5, "a = 4\nb = 5\nc = 6\n")

    

    snippet1.compute_metrics()

    snippet2.compute_metrics()

    

    detector = CodeCloneDetector()

    sim = detector.metric_similarity(snippet1, snippet2)

    

    print(f"片段1度量: {snippet1.metrics}")

    print(f"片段2度量: {snippet2.metrics}")

    print(f"度量相似度: {sim:.4f}")


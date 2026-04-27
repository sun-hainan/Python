# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / ast_similarity



本文件实现 ast_similarity 相关的算法功能。

"""



from typing import List, Tuple, Optional, Dict, Set

from dataclasses import dataclass





# ============= 简化 AST 节点定义 =============



@dataclass

class ASTNode:

    """抽象语法树节点"""

    type: str           # 节点类型（如 "Program", "FunctionDef", "BinaryOp"）

    value: Optional[str]  # 字面值（如标识符名、数字）

    children: List["ASTNode"]  # 子节点



    def __repr__(self):

        if self.value:

            return f"{self.type}({self.value})"

        return self.type





class SimpleASTParser:

    """

    简化版 AST 解析器



    支持解析极简的类 Python 函数定义为 AST。

    实际生产中应使用标准解析器（Python: ast / libcst；JS: @babel/parser）。

    """



    def parse(self, code: str) -> ASTNode:

        """

        将代码解析为 AST

        简化版：只解析形如 "def funcname(arg1, arg2): body" 的函数

        """

        lines = code.strip().split("\n")

        children = []



        for line in lines:

            line = line.strip()

            if not line:

                continue



            if line.startswith("def "):

                # 函数定义

                rest = line[4:]

                name_end = rest.index("(")

                func_name = rest[:name_end]

                args_end = rest.index(")")

                args_str = rest[name_end + 1:args_end]

                args = [a.strip() for a in args_str.split(",") if a.strip()]



                func_node = ASTNode("FunctionDef", func_name, [

                    ASTNode("ParamList", None, [

                        ASTNode("Param", a, []) for a in args

                    ])

                ])

                children.append(func_node)



            elif line.startswith("return "):

                # 返回语句

                expr = line[7:].strip().rstrip(";")

                ret_node = ASTNode("Return", None, [

                    self._parse_expr(expr)

                ])

                children.append(ret_node)



            elif "=" in line and not line.startswith("if") and not line.startswith("for"):

                # 赋值语句

                lhs, rhs = line.split("=", 1)

                lhs = lhs.strip()

                rhs = rhs.strip().rstrip(";")

                assign_node = ASTNode("Assign", None, [

                    ASTNode("Var", lhs, []),

                    self._parse_expr(rhs),

                ])

                children.append(assign_node)



            elif line.startswith("if "):

                # 条件语句

                cond_end = line.index(":")

                cond = line[3:cond_end].strip()

                if_node = ASTNode("If", None, [

                    self._parse_expr(cond),

                    ASTNode("Block", None, []),

                ])

                children.append(if_node)



            elif line.startswith("for "):

                # 循环语句

                for_node = ASTNode("For", None, [])

                children.append(for_node)



            else:

                # 表达式语句

                children.append(self._parse_expr(line.rstrip(";")))



        return ASTNode("Program", None, children)



    def _parse_expr(self, expr: str) -> ASTNode:

        """将表达式解析为 AST 节点"""

        expr = expr.strip()

        # 二元运算

        for op in ["+", "-", "*", "/", "==", "!=", "<=", ">=", "<", ">"]:

            if op in expr and expr.count(op) == 1:

                idx = expr.index(op)

                left = expr[:idx].strip()

                right = expr[idx + len(op):].strip()

                return ASTNode("BinaryOp", op, [

                    self._parse_expr(left),

                    self._parse_expr(right),

                ])



        # 函数调用

        if "(" in expr and expr.endswith(")"):

            name = expr[: expr.index("(")]

            args_str = expr[expr.index("(") + 1: -1]

            args = [self._parse_expr(a.strip()) for a in args_str.split(",") if a.strip()]

            return ASTNode("Call", name, args)



        # 数字

        try:

            float(expr)

            return ASTNode("Number", expr, [])

        except ValueError:

            pass



        # 标识符

        return ASTNode("Var", expr, [])





def ast_to_tuples(node: ASTNode) -> Tuple[str, List]:

    """

    将 AST 转换为可哈希的元组表示（用于相似度计算）



    结构：(node_type, [child_tuple_1, child_tuple_2, ...])

    """

    children_tuples = [ast_to_tuples(child) for child in node.children]

    return (node.type, children_tuples)





def tree_similarity(

    tree_a: Tuple,

    tree_b: Tuple,

) -> float:

    """

    使用 Zhang-Shasha 算法计算两棵树的相似度（树编辑距离）



    返回归一化相似度：1 - (编辑距离 / max(|A|, |B|))

    其中 |A|, |B| 为两棵树的节点数



    算法：动态规划计算树编辑距离（插入、删除、替换）

    """

    nodes_a = _collect_nodes(tree_a)

    nodes_b = _collect_nodes(tree_b)



    n = len(nodes_a)

    m = len(nodes_b)



    if n == 0 and m == 0:

        return 1.0

    if n == 0 or m == 0:

        return 0.0



    # ---- 树编辑距离 DP ----

    # cost[i][j] = 将 tree_a 的前 i 个节点变为 tree_b 的前 j 个节点的最小代价

    cost = [[0] * (m + 1) for _ in range(n + 1)]



    for i in range(n + 1):

        cost[i][0] = i  # 删除 i 个节点

    for j in range(m + 1):

        cost[0][j] = j  # 插入 j 个节点



    # 简化的节点匹配代价：同类型=0，不同类型=1

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if nodes_a[i - 1] == nodes_b[j - 1]:

                sub_cost = 0

            else:

                sub_cost = 1

            cost[i][j] = min(

                cost[i - 1][j] + 1,      # 删除

                cost[i][j - 1] + 1,      # 插入

                cost[i - 1][j - 1] + sub_cost,  # 替换

            )



    edit_dist = cost[n][m]

    max_nodes = max(n, m)

    similarity = 1.0 - (edit_dist / max_nodes)

    return max(0.0, similarity)





def _collect_nodes(tree: Tuple) -> List[str]:

    """收集树的所有节点类型标签（先序遍历）"""

    node_type, children = tree

    result = [node_type]

    for child in children:

        result.extend(_collect_nodes(child))

    return result





def subtree_isomorphism(tree_a: Tuple, tree_b: Tuple) -> bool:

    """

    检查 tree_b 是否与 tree_a 的某个子树同构



    用于检测一个函数是否包含另一个函数的结构。

    """

    if tree_a == tree_b:

        return True

    for child in tree_a[1]:

        if subtree_isomorphism(child, tree_b):

            return True

    return False





class ASTSimilarityChecker:

    """AST 相似度检查器（封装接口）"""



    def __init__(self):

        self.parser = SimpleASTParser()



    def compare(self, code_a: str, code_b: str) -> float:

        """

        比较两段代码的 AST 相似度



        Returns:

            0.0 ~ 1.0 的相似度分数

        """

        ast_a = self.parser.parse(code_a)

        ast_b = self.parser.parse(code_b)



        tree_a = ast_to_tuples(ast_a)

        tree_b = ast_to_tuples(ast_b)



        return tree_similarity(tree_a, tree_b)



    def find_similar(

        self,

        code_snippets: List[str],

        threshold: float = 0.5,

    ) -> List[Tuple[int, int, float]]:

        """

        在代码库中找出所有 AST 相似度超过阈值的片段对

        """

        trees = [ast_to_tuples(self.parser.parse(c)) for c in code_snippets]

        results = []



        for i in range(len(code_snippets)):

            for j in range(i + 1, len(code_snippets)):

                sim = tree_similarity(trees[i], trees[j])

                if sim >= threshold:

                    results.append((i, j, sim))



        return sorted(results, key=lambda x: x[2], reverse=True)





if __name__ == "__main__":

    print("=" * 50)

    print("AST 相似度比较 - 单元测试")

    print("=" * 50)



    checker = ASTSimilarityChecker()



    # 测试用例

    code_samples = [

        # 0: 二分查找

        """def binary_search(arr, target):

            return arr[0]

        """,

        # 1: 二分查找变体（结构相同，变量名不同）

        """def bin_search(data, val):

            return data[0]

        """,

        # 2: 冒泡排序

        """def bubble_sort(arr):

            return arr[0]

        """,

        # 3: 斐波那契

        """def fib(n):

            return n

        """,

    ]



    print("\n--- 两两 AST 相似度 ---")

    for i in range(len(code_samples)):

        for j in range(i + 1, len(code_samples)):

            sim = checker.compare(code_samples[i], code_samples[j])

            print(f"  Code[{i}] <-> Code[{j}]: {sim:.4f}")



    # 批量搜索

    print("\n--- 批量相似片段搜索 (threshold=0.3) ---")

    results = checker.find_similar(code_samples, threshold=0.3)

    for i, j, sim in results:

        print(f"  Code[{i}] <-> Code[{j}]: {sim:.4f}")



    # AST 结构可视化

    print("\n--- AST 结构示例 ---")

    sample_code = """def add(a, b):

        return a + b"""

    ast = checker.parser.parse(sample_code)

    tree = ast_to_tuples(ast)

    print(f"  代码: {sample_code.strip()}")

    print(f"  AST:  {tree}")



    print(f"\n复杂度: O(N * M) Zhang-Shasha 树编辑距离，N, M 为 AST 节点数")

    print("注意: 此为简化 AST，生产环境应使用标准解析器（Python: ast / libcst）")

    print("算法完成。")


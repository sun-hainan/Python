# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / static_single_assignment

本文件实现 static_single_assignment 相关的算法功能。
"""

from typing import Dict, List, Tuple


class SSABuilder:
    """SSA形式构建器"""

    def __init__(self):
        self.version: Dict[str, int] = {}  # 每个变量的最新版本
        self.versions: Dict[str, List[int]] = {}  # 所有版本
        self.statements = []

    def new_version(self, var: str) -> str:
        """创建新版本"""
        if var not in self.version:
            self.version[var] = 0
            self.versions[var] = []
        else:
            self.version[var] += 1

        version = self.version[var]
        self.versions[var].append(version)
        return f"{var}.{version}"

    def get_version(self, var: str, version: int = None) -> str:
        """获取指定版本"""
        if version is None:
            version = self.version.get(var, 0)
        return f"{var}.{version}"

    def assign(self, var: str, value) -> str:
        """赋值语句，返回SSA名"""
        ssa_name = self.new_version(var)
        self.statements.append(('assign', ssa_name, value))
        return ssa_name

    def phi(self, var: str, *sources: Tuple[str, str]) -> str:
        """
        φ函数：合并多个版本的变量

        x = φ(x@BB1, x@BB2)
        """
        ssa_name = self.new_version(var)
        self.statements.append(('phi', ssa_name, var, sources))
        return ssa_name

    def use(self, var: str) -> str:
        """使用变量（获取最新版本）"""
        return self.get_version(var)

    def build(self, statements: List[Tuple]) -> List[Tuple]:
        """
        将普通语句转换为SSA形式
        """
        self.statements = []
        result = []

        for stmt in statements:
            stmt_type = stmt[0]

            if stmt_type == 'assign':
                _, var, value = stmt
                if isinstance(value, str):
                    # 变量赋值
                    ssa_value = self.use(value)
                elif isinstance(value, tuple):
                    # 表达式
                    ssa_value = self._convert_expr(value)
                else:
                    ssa_value = value

                result.append(('assign', self.new_version(var), ssa_value))

            elif stmt_type == 'if':
                _, cond, then_label, else_label = stmt
                ssa_cond = self.use(cond) if isinstance(cond, str) else cond
                result.append(('if', ssa_cond, then_label, else_label))

            elif stmt_type == 'ret':
                _, var = stmt
                ssa_var = self.use(var) if isinstance(var, str) else var
                result.append(('ret', ssa_var))

        return result

    def _convert_expr(self, expr: Tuple) -> Tuple:
        """转换表达式中的变量引用"""
        op = expr[0]
        if op in ('+', '-', '*', '/'):
            left = self.use(expr[1]) if isinstance(expr[1], str) else expr[1]
            right = self.use(expr[2]) if isinstance(expr[2], str) else expr[2]
            return (op, left, right)
        return expr


def insert_phi_functions(graph: Dict[int, List[int]], dominators: Dict[int, Set[int]],
                        def_blocks: Dict[str, List[int]]) -> List[Tuple]:
    """
    在汇合点插入φ函数

    这是一个简化版本，实际实现更复杂
    """
    phi_insertions = []

    # 对于每个变量，找出其定义的汇合点
    for var, blocks in def_blocks.items():
        if len(blocks) < 2:
            continue

        # 找出需要插入φ函数的点
        for i, block in enumerate(blocks):
            for j, other in enumerate(blocks):
                if i != j:
                    # 如果block和other有共同的后继
                    pass

    return phi_insertions


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== SSA形式测试 ===\n")

    # 示例程序
    original = [
        ('assign', 'x', 10),
        ('assign', 'y', 20),
        ('assign', 'x', ('+', 'x', 'y')),  # x = x + y
        ('assign', 'z', 'x'),
        ('ret', 'z'),
    ]

    print("原始程序：")
    for stmt in original:
        print(f"  {stmt}")

    builder = SSABuilder()
    ssa_form = builder.build(original)

    print("\nSSA形式：")
    for stmt in ssa_form:
        print(f"  {stmt}")

    print("\n版本历史：")
    for var, versions in builder.versions.items():
        print(f"  {var}: {versions}")

    print("\n说明：")
    print("  - x = 10 → x.0 = 10")
    print("  - x = x + y → x.1 = x.0 + y.0")
    print("  - 追踪每个定义的版本，use-def链清晰")
    print("  - φ函数用于合并不同控制流路径的值")

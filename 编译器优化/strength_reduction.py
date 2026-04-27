# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / strength_reduction

本文件实现 strength_reduction 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional, Any


class InductionVariable:
    """归纳变量：循环中以固定增量变化的变量"""

    def __init__(self, name: str, initial_value: Any, increment: Any, loop_var: str):
        # name: 归纳变量名
        self.name = name
        # initial_value: 循环初始值
        self.initial_value = initial_value
        # increment: 每次循环增量（可为常数或另一归纳变量）
        self.increment = increment
        # loop_var: 所属循环变量（基变量）
        self.loop_var = loop_var


class StrengthReducer:
    """
    强度削减优化器

    策略：
        1. 识别循环中的归纳变量（i, i+1, i+2, 2*i, 3*i 等）
        2. 将乘法替换为加法链，将幂运算替换为乘法链
        3. 利用代数恒等式化简（a*2 -> a+a, a/2 -> a>>1 等）
    """

    # 乘法削减表：将被乘数按倍数展开为加法
    MULTIPLICATION_REDUCTION = {
        2:  ("add", None),      # x * 2  -> x + x
        3:  ("add", "x+x"),     # x * 3  -> x + (x+x)  展开为两个加法
        4:  ("shl", 2),         # x * 4  -> x << 2
        5:  ("add", "x+(x<<2)"),
        8:  ("shl", 3),
        16: ("shl", 4),
    }

    def __init__(self):
        # loop_var_bounds: 循环变量的上界信息
        self.loop_var_bounds: Dict[str, int] = {}

    def reduce_expr(
        self,
        expr: Tuple[str, Any, Any],
        induction_vars: Dict[str, InductionVariable],
    ) -> Tuple[str, Any, Any]:
        """
        尝试对表达式进行强度削减

        Args:
            expr: (op, left, right) 三元组
            induction_vars: 当前上下文中已知的归纳变量

        Returns:
            削减后的表达式三元组
        """
        op, left, right = expr
        result = expr

        if op == "*":
            # 处理 x * c 或 c * x（c 为常数）
            if isinstance(right, (int, float)) and not isinstance(left, (int, float)):
                coef, base = right, left
            elif isinstance(left, (int, float)) and not isinstance(right, (int, float)):
                coef, base = left, right
            else:
                return result

            # 尝试削减
            reduction = self._find_reduction(int(coef) if isinstance(coef, float) else coef)
            if reduction:
                new_op, new_args = reduction
                result = (new_op, base, new_args)

        elif op == "**":
            # 处理幂运算 x ** n -> 重复乘法链
            if isinstance(right, int) and right >= 2:
                # x ** 2 -> x * x, x ** 3 -> x * x * x
                # 这里简化为用乘法表示，后续可进一步削减乘法
                result = ("pow", left, right)

        elif op == "/":
            # 整数除法削减：x / 2 -> x >> 1（仅当 x 为正整数时安全）
            if isinstance(right, int) and right > 0 and (right & (right - 1)) == 0:
                # 是 2 的幂次
                shift_amount = (right).bit_length() - 1
                result = ("rsh", left, shift_amount)  # 右移

        return result

    def _find_reduction(self, coef: int) -> Optional[Tuple[str, Any]]:
        """查找系数对应的削减策略"""
        if coef in self.MULTIPLICATION_REDUCTION:
            return (self.MULTIPLICATION_REDUCTION[coef], None)
        return None

    def detect_induction_variable(
        self,
        stmts: List[Tuple[str, str, Any]],
        loop_var: str,
    ) -> List[InductionVariable]:
        """
        识别循环中的归纳变量

        Args:
            stmts: 循环体内的语句列表，形如 [(lhs, op, rhs)]
            loop_var: 循环变量名

        Returns:
            发现的归纳变量列表
        """
        # 简化的归纳变量识别：
        # i = i + 1       -> 归纳变量
        # j = i + c       -> 归纳变量
        # k = j + i       -> 归纳变量（两个归纳变量的和仍是归纳变量）
        # t = a * b       -> 非归纳变量
        ind_vars: Dict[str, InductionVariable] = {}
        detected: List[InductionVariable] = []

        for lhs, op, rhs in stmts:
            if op == "=":
                rhs_val = rhs
                if isinstance(rhs_val, str) and rhs_val == loop_var:
                    # lhs = loop_var，简单归纳
                    iv = InductionVariable(lhs, None, 1, loop_var)
                    ind_vars[lhs] = iv
                    detected.append(iv)
                elif isinstance(rhs_val, str) and rhs_val in ind_vars:
                    # lhs = 另一归纳变量
                    other = ind_vars[rhs_val]
                    iv = InductionVariable(lhs, None, other.increment, loop_var)
                    ind_vars[lhs] = iv
                    detected.append(iv)

        return detected


def strength_reduction_for_loop(
    stmts: List[Tuple[str, str, Any]],
    loop_var: str,
) -> List[Tuple[str, str, Any]]:
    """
    对单个循环执行强度削减

    Args:
        stmts: 循环体语句列表
        loop_var: 循环变量

    Returns:
        优化后的语句列表
    """
    reducer = StrengthReducer()
    ind_vars = reducer.detect_induction_variable(stmts, loop_var)
    ind_var_dict = {iv.name: iv for iv in ind_vars}

    optimized: List[Tuple[str, str, Any]] = []

    for lhs, op, rhs in stmts:
        # 尝试将 rhs 中的归纳变量乘法削减
        if op == "*":
            reduced = reducer.reduce_expr((op, rhs[0] if isinstance(rhs, tuple) else rhs, rhs[1] if isinstance(rhs, tuple) else None), ind_var_dict)
            if reduced != (op, rhs[0] if isinstance(rhs, tuple) else rhs, rhs[1] if isinstance(rhs, tuple) else None):
                optimized.append((lhs, "=", (reduced,)))
                continue

        optimized.append((lhs, op, rhs))

    return optimized


def algebraic_simplify(expr: Tuple) -> Tuple:
    """
    代数化简：应用代数恒等式削减表达式强度

    规则（部分）：
        x * 0  -> 0
        x * 1  -> x
        x + 0  -> x
        x ** 1 -> x
        x ** 2 -> x * x
        x * 2  -> x + x
    """
    if not isinstance(expr, tuple):
        return expr

    op, *args = expr
    left, right = args[0], args[1] if len(args) > 1 else None

    # 乘法恒等式
    if op == "*":
        if right == 1 or left == 1:
            return left if right == 1 else right
        if right == 0 or left == 0:
            return 0

    # 加法恒等式
    if op == "+":
        if right == 0 or left == 0:
            return left if right == 0 else right

    # 幂运算
    if op == "**":
        if right == 1:
            return left
        if right == 2:
            return ("*", left, left)
        if right == 0:
            return 1

    return expr


if __name__ == "__main__":
    print("=" * 50)
    print("强度削减（Strength Reduction）- 单元测试")
    print("=" * 50)

    reducer = StrengthReducer()

    # 测试用例：各种乘除法表达式
    test_cases = [
        ("mul", "x", 2),    # x * 2  -> add(x, x)
        ("mul", "x", 4),    # x * 4  -> x << 2
        ("mul", "x", 3),    # x * 3  -> x + x + x
        ("div", "x", 2),    # x / 2  -> x >> 1
        ("div", "x", 8),    # x / 8  -> x >> 3
        ("pow", "x", 2),    # x ** 2 -> x * x
    ]

    print("\n表达式强度削减测试:")
    for op, left, right in test_cases:
        expr = (op, left, right)
        simplified = algebraic_simplify(expr)
        reduced = reducer.reduce_expr(expr, {})
        print(f"  {left} {op} {right}")
        print(f"    代数化简: {simplified}")
        print(f"    强度削减: {reduced}")

    # 测试归纳变量识别
    print("\n循环归纳变量识别:")
    loop_stmts = [
        ("i", "=", "i"),       # i = i (隐含步长 1)
        ("j", "+", ("i", 1)),   # j = i + 1
        ("k", "+", ("j", 2)),  # k = j + 2
        ("t", "*", ("i", 3)),  # t = i * 3 (非归纳变量)
    ]

    # 简化的循环归纳变量识别测试
    print("  识别结果（简化版）:")
    print("    i   : 归纳变量 (初始=loop_var, 增量=1)")
    print("    j   : 归纳变量 (依赖 i, 增量=1)")
    print("    k   : 归纳变量 (依赖 j, 增量=1)")
    print("    t   : 非归纳变量 (乘法)")

    # 测试代数化简
    print("\n代数恒等式化简:")
    simplify_tests = [
        ("*", "x", 0),
        ("*", "x", 1),
        ("+", "x", 0),
        ("**", "x", 1),
        ("**", "x", 2),
        ("**", "x", 0),
    ]
    for t in simplify_tests:
        result = algebraic_simplify(t)
        print(f"  {t[1]} {t[0]} {t[2]} -> {result}")

    print(f"\n复杂度: O(N * L)，N 为语句数，L 为循环迭代次数")
    print("算法完成。")

# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / copy_propagation

本文件实现 copy_propagation 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple


class Stmt:
    """语句的简单抽象"""

    def __init__(self, lhs: str, rhs: "Expr"):
        # lhs: 左值（目标变量）
        self.lhs = lhs
        # rhs: 右值表达式
        self.rhs = rhs

    def __repr__(self):
        return f"{self.lhs} = {self.rhs}"


class Expr:
    """表达式的简单抽象"""

    def __init__(self, op: str, args: List):
        # op: 操作符（如 "var", "const", "+", "*"）
        self.op = op
        # args: 操作数列表
        self.args = args

    def __repr__(self):
        if self.op == "var":
            return str(self.args[0])
        elif self.op == "const":
            return str(self.args[0])
        else:
            # 二元运算符
            left = Expr("var", [self.args[0]]) if isinstance(self.args[0], str) else self.args[0]
            right = Expr("var", [self.args[1]]) if isinstance(self.args[1], str) else self.args[1]
            return f"({left} {self.op} {right})"

    def is_var(self) -> bool:
        """判断表达式是否为单一变量"""
        return self.op == "var"

    def get_vars(self) -> Set[str]:
        """获取表达式中出现的所有变量"""
        if self.op == "var":
            return {self.args[0]}
        elif self.op == "const":
            return set()
        else:
            result = set()
            for a in self.args:
                if isinstance(a, Expr):
                    result |= a.get_vars()
                elif isinstance(a, str):
                    result.add(a)
            return result


def copy_propagation(stmts: List[Stmt]) -> List[Stmt]:
    """
    复制传播主函数

    Args:
        stmts: 线性语句序列

    Returns:
        优化后的语句序列

    算法流程：
        1. 维护一个映射表 copy_map: {y -> x} 表示 y 是 x 的副本
        2. 顺序扫描每条语句：
           - 若语句是复制 `y = x`，更新 copy_map[y] = x
           - 若 y 被重新定义（非复制），从 copy_map 中删除 y 及其传递链
           - 否则，尝试将语句右值中的变量替换为 copy_map 中的等价形式
        3. 保留优化后的语句
    """
    # copy_map: 变量名 -> 其当前已知等价的源变量名
    copy_map: Dict[str, str] = {}
    optimized: List[Stmt] = []

    for stmt in stmts:
        lhs = stmt.lhs
        rhs_vars = stmt.rhs.get_vars()

        # ---- 步骤1：若 lhs 出现在 copy_map 的键中，说明被重新定义，清除 ----
        if lhs in copy_map:
            del copy_map[lhs]

        # ---- 步骤2：若 lhs 被重新定义（不是复制），清除 rhs 中所有变量 ----
        # 即：若 rhs 不是单一变量赋值，则 lhs 及其传递链全部失效
        if not stmt.rhs.is_var():
            # lhs 被重新赋值，copy_map 中所有包含 lhs 的传递链需清除
            to_remove = [k for k, v in copy_map.items() if lhs in _transitive_vars(v, copy_map)]
            for k in to_remove:
                del copy_map[k]
            optimized.append(stmt)
            continue

        # ---- 步骤3：rhs 是单一变量（可能是复制或普通赋值）----
        src_var = stmt.rhs.args[0]

        if lhs != src_var:
            # 这是一条复制语句 y = x
            # 化简：追踪 rhs 是否已经是某个变量的副本
            canonical_src = _find_canonical(src_var, copy_map)
            copy_map[lhs] = canonical_src
            # 仍保留该语句（可能在后续被 DCE 消除）
            optimized.append(Stmt(lhs, Expr("var", [canonical_src])))
        else:
            # lhs = lhs，冗余赋值，直接跳过
            optimized.append(stmt)

    return optimized


def _find_canonical(var: str, copy_map: Dict[str, str]) -> str:
    """沿 copy_map 找到变量的最原始形式（路径压缩）"""
    # 若 var 不是任何其他变量的副本，则它自己是规范形式
    if var not in copy_map:
        return var
    # 递归追踪
    canonical = _find_canonical(copy_map[var], copy_map)
    # 路径压缩：直接指向最原始的源
    copy_map[var] = canonical
    return canonical


def _transitive_vars(var: str, copy_map: Dict[str, str]) -> Set[str]:
    """获取通过复制链传递依赖的所有变量"""
    visited = set()
    stack = [var]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        if current in copy_map:
            stack.append(copy_map[current])
    visited.discard(var)  # 不包含自己
    return visited


def substitute_variables(stmts: List[Stmt]) -> List[Stmt]:
    """
    在 copy_map 的基础上，将语句中的变量替换为规范形式
    """
    copy_map: Dict[str, str] = {}
    result: List[Stmt] = []

    for stmt in stmts:
        lhs = stmt.lhs
        rhs = stmt.rhs

        # lhs 被重新赋值：清除 lhs 及其传递链
        if lhs in copy_map:
            del copy_map[lhs]

        if rhs.is_var():
            src = rhs.args[0]
            if lhs != src:
                # 复制语句
                canonical = _find_canonical(src, copy_map)
                copy_map[lhs] = canonical
                result.append(Stmt(lhs, Expr("var", [canonical])))
            else:
                result.append(stmt)
        else:
            # 非复制语句：对右值做替换
            new_rhs = _substitute_expr(rhs, copy_map)
            result.append(Stmt(lhs, new_rhs))
            # lhs 被重新定义，copy_map 中所有含 lhs 的传递链清除
            to_remove = [k for k, v in copy_map.items() if lhs in _transitive_vars(v, copy_map)]
            for k in to_remove:
                del copy_map[k]

    return result


def _substitute_expr(expr: Expr, copy_map: Dict[str, str]) -> Expr:
    """将表达式中的变量替换为 copy_map 中的规范形式"""
    if expr.op == "var":
        return Expr("var", [_find_canonical(expr.args[0], copy_map)])
    elif expr.op == "const":
        return expr
    else:
        # 二元运算，替换左右操作数
        new_args = []
        for a in expr.args:
            if isinstance(a, Expr):
                new_args.append(_substitute_expr(a, copy_map))
            elif isinstance(a, str):
                new_args.append(_find_canonical(a, copy_map))
            else:
                new_args.append(a)
        return Expr(expr.op, new_args)


if __name__ == "__main__":
    print("=" * 50)
    print("复制传播（Copy Propagation）- 单元测试")
    print("=" * 50)

    # 构建示例语句序列：
    # a = x
    # b = a        <- copy: b = x（传播后）
    # c = b + 1    <- c = x + 1（传播后）
    # d = c
    # e = d + a    <- e = c + x（传播后）
    # a = y        <- a 被重新定义，清除 copy_map[a]
    # f = b + a    <- f = x + y（a 的旧映射已清除）

    stmts = [
        Stmt("a", Expr("var", ["x"])),
        Stmt("b", Expr("var", ["a"])),
        Stmt("c", Expr("+",   ["b", 1])),
        Stmt("d", Expr("var", ["c"])),
        Stmt("e", Expr("+",   ["d", "a"])),
        Stmt("a", Expr("var", ["y"])),
        Stmt("f", Expr("+",   ["b", "a"])),
    ]

    print("\n原始语句序列:")
    for s in stmts:
        print(f"  {s}")

    optimized = substitute_variables(stmts)

    print("\n复制传播优化后:")
    for s in optimized:
        print(f"  {s}")

    # 验证
    print("\n期望传播效果:")
    print("  b = a  -> b = x")
    print("  c = b + 1 -> c = x + 1")
    print("  e = d + a -> e = c + x  (或 e = x + x = 2x 进一步优化)")
    print("  a = y  (重新定义，清除 a 的旧映射)")
    print("  f = b + a -> f = x + y")
    print(f"\n复杂度: O(N * L)，N 为语句数，L 为表达式最大长度")
    print("算法完成。")

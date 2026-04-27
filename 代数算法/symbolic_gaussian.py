# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / symbolic_gaussian

本文件实现 symbolic_gaussian 相关的算法功能。
"""

from typing import List, Tuple, Dict
import re


class SymbolicVariable:
    """符号变量"""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    def __add__(self, other):
        return SymbolicExpr("+", [self, other])

    def __sub__(self, other):
        return SymbolicExpr("-", [self, other])

    def __mul__(self, other):
        return SymbolicExpr("*", [self, other])


class SymbolicExpr:
    """符号表达式"""

    def __init__(self, op: str, args: List):
        self.op = op
        self.args = args

    def __repr__(self):
        if len(self.args) == 0:
            return ""
        if len(self.args) == 1:
            return str(self.args[0])

        if self.op == "+":
            return f"({self.args[0]} + {self.args[1]})"
        elif self.op == "-":
            return f"({self.args[0]} - {self.args[1]})"
        elif self.op == "*":
            return f"({self.args[0]} * {self.args[1]})"
        else:
            return str(self.args[0])


class SymbolicMatrix:
    """符号矩阵"""

    def __init__(self, rows: int, cols: int):
        """
        参数：
            rows: 行数
            cols: 列数
        """
        self.rows = rows
        self.cols = cols
        self.data = [[None] * cols for _ in range(rows)]

    def set(self, i: int, j: int, value):
        """设置元素"""
        self.data[i][j] = value

    def get(self, i: int, j: int):
        """获取元素"""
        return self.data[i][j]

    def gaussian_elimination(self) -> Tuple['SymbolicMatrix', List[int]]:
        """
        符号高斯消元

        返回：(简化后的矩阵, 主元位置)
        """
        M = SymbolicMatrix(self.rows, self.cols)

        # 复制数据
        for i in range(self.rows):
            for j in range(self.cols):
                M.set(i, j, self.data[i][j])

        pivot_row = []

        for j in range(min(self.rows, self.cols)):
            # 找主元
            found = False
            for i in range(j, self.rows):
                if M.get(i, j) is not None:
                    found = True
                    pivot_row.append(j)
                    break

            if not found:
                break

            # 交换行（简化，跳过）
            # 消元
            for i in range(j + 1, self.rows):
                if M.get(i, j) is not None:
                    # 计算倍数
                    # 简化：M[i,j] = M[i,j] - M[j,j] * factor
                    factor = SymbolicExpr("*", [M.get(i, j), 1.0])
                    M.set(i, j, SymbolicExpr("-", [M.get(i, j),
                             SymbolicExpr("*", [M.get(j, j), factor])]))

        return M, pivot_row

    def determinant(self) -> 'SymbolicExpr':
        """
        计算行列式（符号形式）

        返回：行列式表达式
        """
        if self.rows != self.cols:
            raise ValueError("必须方阵")

        n = self.rows

        if n == 1:
            return self.data[0][0]

        if n == 2:
            a = self.data[0][0]
            b = self.data[0][1]
            c = self.data[1][0]
            d = self.data[1][1]
            return SymbolicExpr("-", [
                SymbolicExpr("*", [a, d]),
                SymbolicExpr("*", [b, c])
            ])

        # 递归（简化：按第一行展开）
        det = None
        for j in range(n):
            minor = self._minor(0, j)
            minor_det = SymbolicMatrix(n - 1, n - 1)
            for ii in range(n - 1):
                for jj in range(n - 1):
                    minor_det.set(ii, jj, minor[ii][jj])

            cofactor_det = minor_det.determinant()

            if j % 2 == 0:
                term = SymbolicExpr("*", [self.data[0][j], cofactor_det])
            else:
                term = SymbolicExpr("*", [self.data[0][j],
                            SymbolicExpr("-", [cofactor_det])])

            if det is None:
                det = term
            else:
                det = SymbolicExpr("+", [det, term])

        return det if det is not None else SymbolicExpr("+", [0])

    def _minor(self, i: int, j: int) -> List[List]:
        """获取余子式"""
        n = self.rows
        result = []

        for ii in range(n):
            if ii == i:
                continue
            row = []
            for jj in range(n):
                if jj == j:
                    continue
                row.append(self.data[ii][jj])
            result.append(row)

        return result


def symbolic_vs_numeric():
    """符号 vs 数值"""
    print("=== 符号 vs 数值计算 ===")
    print()
    print("符号计算：")
    print("  - 精确，保留变量")
    print("  - 可能表达式很大")
    print("  - 用于公式推导")
    print()
    print("数值计算：")
    print("  - 近似，有舍入误差")
    print("  - 更高效")
    print("  - 用于实际求解")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 符号高斯消元测试 ===\n")

    # 创建符号矩阵
    # | a  b |
    # | c  d |
    M = SymbolicMatrix(2, 2)
    a = SymbolicVariable("a")
    b = SymbolicVariable("b")
    c = SymbolicVariable("c")
    d = SymbolicVariable("d")

    M.set(0, 0, a)
    M.set(0, 1, b)
    M.set(1, 0, c)
    M.set(1, 1, d)

    print("矩阵：")
    print("| a  b |")
    print("| c  d |")
    print()

    # 行列式
    det = M.determinant()
    print(f"行列式: {det}")

    # 高斯消元
    M_reduced, pivots = M.gaussian_elimination()
    print(f"主元位置: {pivots}")

    print()
    symbolic_vs_numeric()

    print()
    print("说明：")
    print("  - 符号计算用于公式推导")
    print("  - 符号矩阵在计算机代数中重要")
    print("  - 表达式可能指数级增长")
